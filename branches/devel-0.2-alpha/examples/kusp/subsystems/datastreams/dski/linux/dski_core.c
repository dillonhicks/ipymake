/*
 * stuff for people todo:
 *
 * 	1) test more code paths through entity configure
 * 		- e.g. enable and then reconfigure a histogram
 *
 * 	2) document use of rcu. some of the uses are not explicit
 * 		- e.g. user->chan
 *
 * 	3) check use of sychronize_sched in destroy_filter()
 * 	4) setup kref for contexts...what can go wrong with multi-threaded uses
 * 	   of a context?
 *
 * 	5) create multi-channel per-user/context support
 * 	6) enable read/mmap versions of channels
 * 	7) KERNEL MARKERS IN VANILLA??
 * 	9) general code cleanup and comments
 * 	11) try logging extra data after logging the trigger event for the ed
 * 	chunks
 * 	12) run through comments/rcu stuff for new channel layout
 * 	13) timer synchronization
 * 	14) finish channel close print stats
 */
#include <linux/list.h>
#include <linux/bitmap.h>
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/debugfs.h>
#include <linux/spinlock.h>
#include <linux/miscdevice.h>
#include <linux/rcupdate.h>
#include <linux/limits.h>
#include <linux/time.h>
#include <linux/timer.h>
#include <asm/uaccess.h>
#include <asm/semaphore.h>

#include <linux/dski.h>
#include <datastreams/entity.h>
#include <datastreams/dski.h>
#include "dski_common.h"


/* used to generated dstrm_user->name string */
static unsigned int ctxtcnt;
#define CTXT_PREFIX "dski"

struct semaphore dski_mutex;
/* root debugfs dir */
static struct dentry *rootdir;

/*
 * find_datastream - search list of datastreams assoc. with an instance
 *
 * @inst:	datastream instance to search within
 * @name	name to match
 *
 * Returns pointer to matching datastream, else NULL
 */
struct datastream *find_datastream(struct dstrm_user *user, char *name)
{
	struct datastream *datastream;

	list_for_each_entry(datastream, &user->datastreams, list)
		if (strcmp(datastream->name, name) == 0)
			return datastream;
	return NULL;
}



struct datastream_list *
datastream_list_remove(struct datastream_list **list, struct datastream *d)
{
	struct datastream_list **next = list, *check;

	down(&dski_mutex);

	while ((check = *next)) {
		if (check->datastream == d) {
			rcu_assign_pointer(*next, check->next);
			break;
		}
		next = &check->next;
	}

	up(&dski_mutex);
	return check;
}

static int datastream_assign_channel(struct dstrm_user *user,
		char *name, int channel_id)
{
	struct datastream *d;
	struct dstrm_channel *d_chan;

	d = find_datastream(user, name);
	if (!d) {
		printk("dski: can't find datastream %s\n", name);
		return -EINVAL;
	}

	if (d->d_chan) {
		printk("dski: datastream %s already assigned to another channel\n",
				name);
		return -EBUSY;
	}

	if (list_empty(&user->channels)) {
		printk("dski: channel %d doesn't exist", channel_id);
		return -EINVAL;
	}
	
	list_for_each_entry(d_chan, &user->channels, list) {
		if (d_chan->channel_id == channel_id)
			break;
	}

	if (d_chan->channel_id != channel_id) {
		printk("dski: channel %d doesn't exist", channel_id);
		return -EINVAL;
	}

	d->d_chan = d_chan;
	return 0;
}

/*
 * datastream_create: - create and add a datastream to an instance
 *
 * @inst:	instance to which the datastream will attach
 * @name:	name of the new datastream
 *
 * Return 0 on success, negative value otherwise
 *
 * Creates a datastream identified by @name and adds it to the instance's list
 * of datastreams. According to the namespace associated with the instance,
 * datastream-level persistent storage may be allocated. The new datastream will
 * be listed in the datastreams directory for the given instance.
 */
static int datastream_create(struct dstrm_user *user, char *name)
{
	struct datastream *dstrm;
	int ret;

	ret = -EEXIST;
	if (find_datastream(user, name))
		goto out;

	ret = -ENOMEM;
	dstrm = kzalloc(sizeof(*dstrm), GFP_KERNEL);
	if (!dstrm)
		goto out;

	dstrm->name = kzalloc(sizeof(char)*(strlen(name)+1), GFP_KERNEL);
	if (!dstrm->name)
		goto out_free;

	dstrm->user = user;
	dstrm->d_chan = NULL;
/*********FIXME.J****TEMPORARY_DEVEL_STEP*********/
	clear_bit(DS_DSTRM_ON, &dstrm->flags);
/*********FIXME.J****TEMPORARY_DEVEL_STEP*********/
	strcpy(dstrm->name, name);
	INIT_LIST_HEAD(&dstrm->enabled);
	INIT_LIST_HEAD(&dstrm->filters);
	list_add(&dstrm->list, &user->datastreams);

	printk("dski (%s): create datastream [%s]\n", user->name, name);

	return 0;

out_free:
	kfree(dstrm->name);
	kfree(dstrm);
out:
	return ret;
}

int __datastream_destroy(struct dstrm_user *user, struct datastream *d)
{
	struct datastream_list *link, *tmp;

	printk("dski (%s): destroy datastream [%s]\n", user->name, d->name);

	/* disable all entities logging to this datastream */
	list_for_each_entry_safe(link, tmp, &d->enabled, list) {
		BUG_ON(link->datastream != d);
		__entity_disable(link->datastream, link->ip);
	}

	printk("all entities disabled\n");

	/* __entity_disable removes d->enabled list entries */
	BUG_ON(!list_empty(&d->enabled));
	list_del(&d->list);
	destroy_filters(d);
	kfree(d->name);
	kfree(d);

	printk( "datastream destroy done\n");

	return 0;
}

static int datastream_destroy(struct dstrm_user *user, char *name)
{
	struct datastream *d;

	printk("enter datastream_destroy\n");

	d = find_datastream(user, name);
	if (!d) {
		return -EINVAL;
	}

	return __datastream_destroy(user, d);
}

static int datastream_enable(struct dstrm_user *user, char *name)
{
	struct datastream *d;

	printk("enter datastream_enable\n");

	d = find_datastream(user, name);
	if (!d) {
		return -EINVAL;
	}

	printk("dski (%s): enable datastream [%s]\n", user->name, d->name);

	set_bit(DS_DSTRM_ON, &d->flags);

	return 0;
}

static int datastream_disable(struct dstrm_user *user, char *name)
{
	struct datastream *d;

	printk("enter datastream_disable\n");

	d = find_datastream(user, name);
	if (!d) {
		return -EINVAL;
	}

	printk("dski (%s): disable datastream [%s]\n", user->name, d->name);

	clear_bit(DS_DSTRM_ON, &d->flags);

	return 0;
}

static long dski_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
	union dski_ioctl_param param;
	struct dski_ioc_entity_ctrl *ectrl;
	struct dstrm_user *user = filp->private_data;
	int ret = 0;

	if (copy_from_user(&param, (void*)arg, _IOC_SIZE(cmd)))
		return -EFAULT;

	down(&user->mutex);

	switch (cmd) {
	case DSKI_DS_CREATE:
		ret = datastream_create(user, param.datastream_ctrl.name);
		break;

	case DSKI_DS_DESTROY:
		ret = datastream_destroy(user, param.datastream_ctrl.name);
		break;

	case DSKI_DS_ENABLE:
		ret = datastream_enable(user, param.datastream_ctrl.name);
		break;

	case DSKI_DS_DISABLE:
		ret = datastream_disable(user, param.datastream_ctrl.name);
		break;

	case DSKI_CHANNEL_OPEN:
		ret = channel_open(user, param.channel_ctrl.subbuf_size,
				param.channel_ctrl.num_subbufs,
				param.channel_ctrl.timeout,
				param.channel_ctrl.flags);
		break;
	
	case DSKI_CHANNEL_CLOSE:
		ret = channel_close(user, param.channel_ctrl.channel_id);
		break;

	case DSKI_CHANNEL_FLUSH:
		ret = channel_flush(user, param.channel_ctrl.channel_id);
		break;

	case DSKI_DS_ASSIGN_CHAN:
		ret = datastream_assign_channel(user,
				param.datastream_ctrl.name,
				param.datastream_ctrl.channel_id);
		break;

	case DSKI_FILTER_APPLY:
		ret = create_filter(user, param.filter_ctrl.datastream,
				param.filter_ctrl.filtername,
				&param.filter_ctrl.params);
		break;

	case DSKI_ENTITY_CONFIGURE:
	{
		union ds_entity_info entity_info;

		ectrl = &param.entity_ctrl;

		ret = -EINVAL;
		if (ectrl->flags & ENTITY_ENABLE &&
				ectrl->flags & ENTITY_DISABLE)
			goto out;

		if (ectrl->config_info) {
			if (copy_from_user(&entity_info, ectrl->config_info,
						sizeof(entity_info))) {
				ret = -EFAULT;
				goto out;
			}

			ectrl->config_info = &entity_info;
		}

		if (ectrl->flags & ENTITY_ENABLE)
			ret = entity_enable(user, ectrl->datastream, ectrl->id,
					ectrl->config_info);

		else if (ectrl->flags & ENTITY_DISABLE)
			ret = entity_disable(user, ectrl->datastream, ectrl->id);

		else
			if (!ectrl->config_info)
				ret = -EINVAL;
			else
				ret = entity_configure(user, ectrl->datastream,
						ectrl->id, ectrl->config_info);
		break;
	}

	case DSKI_RELAY_DIR:
		if (copy_to_user((void*)arg, user->name, strlen(user->name)+1))
			ret = -EFAULT;
		break;

	case DSKI_IPS_QUERY:
	{
		const struct __datastream_ip *ip;
		struct dski_ioc_datastream_ip_info info, *pos;
		size_t size = 0;

		pos = param.ip_info.info;
		dski_update_list();

		mutex_lock(&dski_ips_lock);
		list_for_each_entry(ip, &dski_ips_list, list_entry) {
			
			size += sizeof(info);
			if (size > param.ip_info.size)
				continue;

			strncpy(info.group, ip->group, DS_STR_LEN);
			strncpy(info.name, ip->name, DS_STR_LEN);
			info.type = ip->type;
			info.id = ip->id;

			if (ip->edf)
				strncpy(info.edf, ip->edf, DS_STR_LEN);
			else
				info.edf[0] = '\0';

			snprintf(info.desc, DS_STR_LEN, "%s:%s:%d",
				ip->file, ip->func, ip->line);
		
			if (copy_to_user(pos, &info, sizeof(info))) {
				mutex_unlock(&dski_ips_lock);
				ret = -EFAULT;
				goto out;
			}
			pos++;
		}
		mutex_unlock(&dski_ips_lock);

		param.ip_info.size = size;
		if (copy_to_user((void*)arg, &param.ip_info,
					sizeof(param.ip_info)))
			ret = -EFAULT;
		break;
	}

	default:
		ret = -ENOTTY;
		break;
	}

	up(&user->mutex);
out:
	return ret;
}

/* FIXME: this doesnt sufficiently clean up in some situations */
static int dski_release(struct inode *inode, struct file *filp)
{
	struct dstrm_channel *d_chan, *tmp;
	struct datastream *d, *dtmp;
	struct dstrm_user *user = filp->private_data;

	down(&user->mutex);

	list_for_each_entry_safe(d_chan, tmp, &user->channels, list)
		__channel_close(user, d_chan);

	list_for_each_entry_safe(d, dtmp, &user->datastreams, list)
		__datastream_destroy(user, d);

	BUG_ON(!list_empty(&user->datastreams));
	BUG_ON(!list_empty(&user->channels));

	debugfs_remove(user->dir);
	up(&user->mutex);

	printk("dski: releasing '%s'\n", user->name);

	kfree(user->name);
	kfree(user);

	return 0;
}

/*
 * dski_open - open call for datastream device
 *
 * Create a separate context for this user
 */
static int dski_open(struct inode *inode, struct file *filp)
{
	struct dstrm_user *user;
	char buf[NAME_MAX];
	int ret;

	down(&dski_mutex);

	/* storage for context structure */
	ret = -ENOMEM;
	user = kmalloc(sizeof(*user), GFP_KERNEL);
	if (!user)
		goto out;

	/* assumed on user->dir error path */
	user->dir = NULL;

	/* generated name */
	ret = snprintf(buf, NAME_MAX, "%s%u", CTXT_PREFIX, ++ctxtcnt);
	if (ret >= NAME_MAX) {
		ret = -ENOSPC;
		goto out;
	}

	/* directory for context */
	user->dir = debugfs_create_dir(buf, rootdir);
	if (IS_ERR(user->dir)) {
		printk("dski: could not create dir '%s'\n", buf);
		ret = -EAGAIN;
		goto out;
	}

	/* space for the name (ret from snprintf is used here */
	user->name = kmalloc(sizeof(char)*(ret+1), GFP_KERNEL);
	if (!user->name) {
		ret = -ENOMEM;
		goto out;
	}

	strcpy(user->name, buf);
	sema_init(&user->mutex, 1);
	user->num_channels = 0;
	
	/* access to this context */
	filp->private_data = user;
	
	/* datastreams managed within context */
	INIT_LIST_HEAD(&user->datastreams);
	INIT_LIST_HEAD(&user->channels);
	
	printk("dski: opening device [%s]\n", user->name);
	up(&dski_mutex);
	return 0;

out:
	up(&dski_mutex);
	if (user && user->dir)
		debugfs_remove(user->dir);
	kfree(user);
	return ret;
}

static struct file_operations dski_dev_fops = {
	.owner		= THIS_MODULE,
	.open		= dski_open,
	.release 	= dski_release,
	.unlocked_ioctl	= dski_ioctl
};

static struct miscdevice dski_misc = {
	.minor = MISC_DYNAMIC_MINOR,
	.name = "dski",
	.fops = &dski_dev_fops
};

/*
 * dski_debugfs_init - initialize debugfs base interface
 */
static int dski_debugfs_init(void)
{
	int ret;

	ret = misc_register(&dski_misc);
	if (ret)
		return ret;

	rootdir = debugfs_create_dir(DSKI_DIR, NULL);
	if (IS_ERR(rootdir))
		goto out;

	return 0;

out:
	printk("dski: debugfs_create_dir '%s' failed!\n", DSKI_DIR);
	if (rootdir)
		debugfs_remove(rootdir);

	return -1;
}

static int __init dski_init(void)
{
#ifdef CONFIG_DSKI_HASH_TABLE
	struct list_head *cur;
	int i;
#endif

	sema_init(&dski_mutex, 1);

	if (dski_debugfs_init())
		return -EINVAL;

	dskihooks.ds_event_log = event_log;
	dskihooks.ds_counter_add = counter_add;
	dskihooks.ds_counter_log = counter_log;
	dskihooks.ds_counter_reset = counter_reset;
	dskihooks.ds_interval_start = interval_start;
	dskihooks.ds_interval_end = interval_end;
	dskihooks.ds_histogram_add = histogram_add;
	dskihooks.ds_histogram_log = histogram_log;
	dskihooks.ds_histogram_reset = histogram_reset;
	dskihooks.ds_user_data_log = user_data_log;

#ifdef CONFIG_DSKI_HASH_TABLE
	/* Initialize DSKI IPs table table */
/*
	dski_ips_table = kmalloc((sizeof(struct list_head *) * DSKI_TABLE_SIZE), GFP_KERNEL);
	for (i = 0; i < DSKI_TABLE_SIZE; i++) {
		dski_ips_table[i] = kmalloc(sizeof(struct list_head), GFP_KERNEL);
		LIST_HEAD(dski_ips_table[i]);
	}
*/
	for (i = 0; i < DSKI_TABLE_SIZE; i++) {
		cur = &(dski_ips_table[i]);
		INIT_LIST_HEAD(cur);
	}
#endif

#ifdef CONFIG_DSKI_DEFERRED
	INIT_WORK(&deferred_data.dski_deferred, dski_deferred_function);
#endif

	printk("dski: DSKI INITIALIZED\n");

	return 0;
}

static void __exit dski_exit(void)
{
	if (rootdir)
		debugfs_remove(rootdir);
	misc_deregister(&dski_misc);
}

module_init(dski_init);
module_exit(dski_exit);
MODULE_LICENSE("GPL");
