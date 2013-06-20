#include <linux/relay.h>
#include <linux/list.h>
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/debugfs.h>
#include <linux/module.h>

#include "dski_common.h"

#define CHAN_PREFIX "chan"

/* Max buffer space per-channel per-user */
#define RELAY_BUF_MAX		((size_t)(1<<25))



/******* MMAP ***********************/
static struct dentry	*produced_control[NR_CPUS];
static struct dentry	*consumed_control[NR_CPUS];
struct file_operations	produced_fops;
struct file_operations	consumed_fops;

/**
 *	remove_channel_controls - removes produced/consumed control files
 */
static void remove_channel_controls(void)
{
	int i;

	printk("dski: remove_channel_controls\n");

	for (i = 0; i < NR_CPUS; i++) {
		if (produced_control[i]) {
			debugfs_remove(produced_control[i]);
			produced_control[i] = NULL;
			continue;
		}
		break;
	}

	for (i = 0; i < NR_CPUS; i++) {
		if (consumed_control[i]) {
			debugfs_remove(consumed_control[i]);
			consumed_control[i] = NULL;
			continue;
		}
		break;
	}
}

/**
 *	create_channel_controls - creates produced/consumed control files
 *
 *	Returns channel on success, negative otherwise.
 */
static int create_channel_controls(struct dentry *parent,
				   const char *base_filename,
				   struct rchan *chan)
{
	unsigned int i;
	int mode = S_IROTH | S_IWOTH;

	char *tmpname = kmalloc(NAME_MAX + 1, GFP_KERNEL);
	if (!tmpname)
		return -ENOMEM;

	printk("dski: create_channel_controls\n");


	for_each_online_cpu(i) {
		sprintf(tmpname, "%s%d.produced", base_filename, i);

		produced_control[i] = debugfs_create_file(tmpname, mode, 
				parent, chan->buf[i], &produced_fops);
		if (!produced_control[i]) {
			printk("dski: Couldn't create relayfs control file %s.\n",
			       tmpname);
			goto cleanup_control_files;
		}

		sprintf(tmpname, "%s%d.consumed", base_filename, i);
		consumed_control[i] = debugfs_create_file(tmpname, mode, 
				parent, chan->buf[i], &consumed_fops);
		if (!consumed_control[i]) {
			printk("dski: Couldn't create relayfs control file %s.\n",
			       tmpname);
			goto cleanup_control_files;
		}
	}

	return 0;

cleanup_control_files:
	remove_channel_controls();
	return -ENOMEM;
}


/*
 * control files for relayfs produced/consumed sub-buffer counts
 */

static int produced_open(struct inode *inode, struct file *filp)
{
	filp->private_data = inode->i_private;

	return 0;
}

static ssize_t produced_read(struct file *filp, char __user *buffer,
			     size_t count, loff_t *ppos)
{
	struct rchan_buf *buf = filp->private_data;

	return simple_read_from_buffer(buffer, count, ppos,
				       &buf->subbufs_produced,
				       sizeof(buf->subbufs_produced));
}

/*
 * 'produced' file operations - r, binary
 *
 *  There is a .produced file associated with each per-cpu relayfs file.
 *  Reading a .produced file returns the number of sub-buffers so far
 *  produced for the associated relayfs buffer.
 */
struct file_operations produced_fops = {
	.owner =	THIS_MODULE,
	.open =		produced_open,
	.read =		produced_read
};

static int consumed_open(struct inode *inode, struct file *filp)
{
	filp->private_data = inode->i_private;
	
	return 0;
}

static ssize_t consumed_read(struct file *filp, char __user *buffer,
			     size_t count, loff_t *ppos)
{
	struct rchan_buf *buf = filp->private_data;


	return simple_read_from_buffer(buffer, count, ppos,
				       &buf->subbufs_consumed,
				       sizeof(buf->subbufs_consumed));
}

static ssize_t consumed_write(struct file *filp, const char __user *buffer,
			      size_t count, loff_t *ppos)
{
	struct rchan_buf *buf = filp->private_data;
	size_t consumed;

	if (copy_from_user(&consumed, buffer, sizeof(consumed)))
		return -EFAULT;
		
	relay_subbufs_consumed(buf->chan, buf->cpu, consumed);

	return count;
}

/*
 * 'consumed' file operations - r/w, binary
 *
 *  There is a .consumed file associated with each per-cpu relayfs file.
 *  Writing to a .consumed file adds the value written to the
 *  subbuffers-consumed count of the associated relayfs buffer.
 *  Reading a .consumed file returns the number of sub-buffers so far
 *  consumed for the associated relayfs buffer.
 */
struct file_operations consumed_fops = {
	.owner =	THIS_MODULE,
	.open =		consumed_open,
	.read =		consumed_read,
	.write =	consumed_write,
};



/******** RELAYFS CALLBACKS ***********/

/*
 * subbuf_start_handler - callback from relay noting that the current
 * sub-buffer is full and that it would like to switch to the next
 * sub-buffer.
 *
 * returns a boolean value indicating whether the switch to the next
 * buffer should be made; a 0 means that data is unfortunately lost.
 */

static int subbuf_start_handler_read(struct rchan_buf *buf, void *subbuf,
		void *prev_subbuf, unsigned int prev_padding)
{

	if (relay_buf_full(buf)) {
		/* Data lost! This gets caught in __event_log
		 * and chan->bufswitchfail is incremented */
		return 0;
	}

	return 1;
}


static int subbuf_start_handler_mmap(struct rchan_buf *buf, void *subbuf,
		void *prev_subbuf, unsigned int prev_padding)
{
	if (prev_subbuf) {
		*((unsigned *)prev_subbuf) = prev_padding;
	}

	if (relay_buf_full(buf)) {
		/* Data lost! This gets caught in __event_log
		 * and chan->bufswitchfail is incremented */
		return 0;
	}

	subbuf_start_reserve(buf, sizeof(unsigned int));
	return 1;
}




/*
 * create_buf_file_handler - called once for each per-cpu buffer from
 * relay_open(). here we create the file which will be used to represent
 * the corresponding channel buffer for that cpu
 */
static struct dentry *create_buf_file_handler(const char *filename,
		struct dentry *parent, int mode, struct rchan_buf *buf,
		int *is_global)
{
	struct dentry *buf_file;

	printk("dski: create_buf_file_handler (%s)\n", filename);

	
	mode = S_IROTH | S_IWOTH;
	buf_file = debugfs_create_file(filename, mode, parent, buf,
				       &relay_file_operations);

	return buf_file;
}

/*
 * remove_buf_file_handler - remove a buffer file from debugfs
 */
static int remove_buf_file_handler(struct dentry *dentry)
{
	printk("dski: remove_buf_file_handler\n");
	debugfs_remove(dentry);
	return 0;
}

static struct rchan_callbacks relayfs_callbacks_read =
{
	.subbuf_start = subbuf_start_handler_read,
	.create_buf_file = create_buf_file_handler,
	.remove_buf_file = remove_buf_file_handler,
};

static struct rchan_callbacks relayfs_callbacks_mmap =
{
	.subbuf_start = subbuf_start_handler_mmap,
	.create_buf_file = create_buf_file_handler,
	.remove_buf_file = remove_buf_file_handler,
};

/*
 * channel_close_timer - fired to close down a channel
 *
 * Used as a saftey mechanism. The executive thread (dski daemon) should set the
 * timer when she opens the channel. Even though the timer is optional, if
 * the executive thread for some reason cannot run to end logging (e.g. system
 * load) then this will force the close of the channel
 */
static void channel_close_timer(unsigned long arg)
{
#if 0
	struct dstrm_user *user = (struct dstrm_user *)arg;

	return;
	if (user->d_chan && user->d_chan->r_chan) {
		relay_close(user->d_chan->r_chan);
		user->chan = NULL;
	}
#endif
}

/*
 * channel_open - open a channel for logging
 *
 * @user:	- user context
 * @bufsize:	- per-cpu buffer size
 * @nbufs:	- number of buffers per cpu
 * @timeout:	- # of seconds to wait until closing channel
 *
 * Opens a relay channel and places per-cpu files into the user's directory in
 * debugfs (user->dir). The files can be used by the dski daemon to log data and
 * will only contain logged entities which have been enabled by this user
 */
int channel_open(struct dstrm_user *user, size_t bufsize,
		size_t nbufs, int timeout, unsigned int flags)
{
	//struct timeval timeval;
	struct dstrm_channel *d_chan;
	char buf[NAME_MAX];
	int ret;

	int mmap_used = (flags & DS_CHAN_MMAP);

	if ((bufsize * nbufs) > RELAY_BUF_MAX || timeout < 0 ||
			bufsize < (sizeof(struct ds_extra_data_chunk) + MIN_EDC)) {
		printk("dski: buffer size parameters bogus\n");
		return -EINVAL;
	}

	/* two flags, exactly one must be set */
	if (flags & DS_CHAN_TRIG && flags & DS_CHAN_CONT) {
		printk("dski: bad flags passed to channel_open\n");
		return -EINVAL;
	}

	d_chan = kmalloc(sizeof(*d_chan), GFP_KERNEL);
	if (!d_chan)
		return -ENOMEM;

	memset(d_chan->seq, 0, sizeof(d_chan->seq));
	atomic_set(&d_chan->edc_writes, 0);
	atomic_set(&d_chan->bufswitchfail, 0);
	d_chan->edc_bytes = 0;
	d_chan->max_data_len = 0;

	d_chan->flags = flags;
	d_chan->user = user;
	d_chan->timer.data = (unsigned long)d_chan;
	d_chan->timer.function = channel_close_timer;
	
	d_chan->channel_id = ++user->num_channels;

	ret = snprintf(buf, NAME_MAX, "%s%d", CHAN_PREFIX, d_chan->channel_id);
	if (ret >= NAME_MAX) {
		printk("dski: path name is too long\n");
		kfree(d_chan);
		return -ENOSPC;
	}

	/* Create the directory structure to contain the relay files
	 * within debugFS */
	d_chan->dir = debugfs_create_dir(buf, user->dir);
	if (IS_ERR(d_chan->dir)) {
		printk("dski: couldn't create directory structure\n");
		kfree(d_chan);
		return -EAGAIN;
	}

	/* Create the relay channel, along with its per-cpu channel buffers */
	d_chan->r_chan = relay_open("cpu", d_chan->dir, bufsize, nbufs,
			(mmap_used ? &relayfs_callbacks_mmap 
			           : &relayfs_callbacks_read), NULL);

	if (!d_chan->r_chan) {
		printk("dski: relay_open failed\n");
		kfree(d_chan);
		return -EAGAIN;
	}

	if (mmap_used) {
		printk("dski: opening channel in mmap mode\n");
		ret = create_channel_controls(d_chan->dir, "cpu", d_chan->r_chan);
		if (ret) {
			kfree(d_chan);
			return ret;
		}
	} else {
		printk("dski: opening channel in read mode\n");
	}

	list_add(&d_chan->list, &user->channels);

	/* <old-comments>
	 * Triggered channels have their timers started at start time
	 *
	 * Commented out, doesn't work properly
	 *
	 * Might want to change the way timers work,
	 * want them to go off in such a way that it doesn't
	 * matter if scheduling of dskid is FUBAR
	 * </old-comments>
	 *
	 * One problem may be if we chose to close the relay_fs channel
	 * when the timer goes off, the threads at user level reading the
	 * per-cpu data and writing it to a file might lose lots of data
	 * or be unhappy in some way.
	 */
	if (!(flags & DS_CHAN_TRIG) && timeout) {
//		timeval.tv_usec = 0;
//		timeval.tv_sec = timeout;
//		d_chan->timer.expires = jiffies + timeval_to_jiffies(&timeval)+1;
//		add_timer(&d_chan->timer);
	}
	
	return d_chan->channel_id;
}

static void channel_print_stats(struct dstrm_user *user, struct dstrm_channel *chan)
{
	unsigned long long seqs;
	int i, fail;

	fail = atomic_read(&chan->bufswitchfail);

	printk("dski  (%s) chan (%d): dropped %d\n", user->name,
				chan->channel_id, fail);
	for (i = 0; i < NR_CPUS; i++) {
		seqs = seqs + chan->seq[i];
		printk("dski (%s) chan (%d): cpu%d seq %llu\n", user->name,
				chan->channel_id, i, chan->seq[i]);
	}
}

int __channel_close(struct dstrm_user *user, struct dstrm_channel *d_chan)
{
	struct datastream *d, *tmp;

	printk("dski: channel_close\n");

	/* disable datastreams which are using this channel */
	list_for_each_entry_safe(d, tmp, &user->datastreams, list) {
		if (d->d_chan == d_chan)
			__datastream_destroy(user, d);
	}

	/*
	 * datastream_destroy does RCU synchronization for all instrumentation
	 * points. we can assume now that there is no possible way (via IPs)
	 * for a code path to try and log to this channel, so its safe to close
	 */
	BUG_ON(!d_chan->r_chan);
	relay_flush(d_chan->r_chan);

	relay_close(d_chan->r_chan);

	remove_channel_controls();

	/* FIXME: fails with 'directory not empty' */
	debugfs_remove(d_chan->dir);

	channel_print_stats(user, d_chan);
	list_del(&d_chan->list);
	
//	if (timer_pending(&d_chan->timer))
//		del_timer_sync(&d_chan->timer);

	return 0;
}

int channel_close(struct dstrm_user *user, int channel_id)
{
	struct dstrm_channel *d_chan;

	if (list_empty(&user->channels)) {
		printk("dski: no channels exist\n");
		return -EINVAL;
	}

	list_for_each_entry(d_chan, &user->channels, list)
		if (d_chan->channel_id == channel_id)
			break;


	if (d_chan->channel_id != channel_id) {
		printk("dski: channel (%d) doesn't exist, can't close it\n",
				channel_id);
		return -EINVAL;
	}

	return __channel_close(user, d_chan);
}

int channel_flush(struct dstrm_user *user, int channel_id)
{
	struct dstrm_channel *d_chan;

	if (list_empty(&user->channels)) {
		printk("dski: no channels exist\n");
		return -EINVAL;
	}

	list_for_each_entry(d_chan, &user->channels, list)
		if (d_chan->channel_id == channel_id)
			break;


	if (d_chan->channel_id != channel_id) {
		printk("dski: channel (%d) doesn't exist, can't close it\n",
				channel_id);
		return -EINVAL;
	}

	relay_flush(d_chan->r_chan);

	return 0;
}

