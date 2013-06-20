#include <cmath>
#include <strings.h>
#include <gsl/gsl_randist.h>
#include "rdist.hpp"
#include "cfgu.h"

namespace rdist
{
	Distribution* config(cfgu::Object dist)
	{
		Distribution* ret = NULL;

		const char* dist_name = dist.get("distribution").str();

		if (!strcasecmp(dist_name, "normal")) {
			ret = new Normal(
					 dist.get("mean").real(),
					 dist.get("variance").real()
					 );
			printf("Created normal distribution: mean=%f variance=%f\n",
			       ((Normal*)ret)->mMean, ((Normal*)ret)->mVariance);
		}

		if (!strcasecmp(dist_name, "uniform")) {
			ret = new Uniform(
					  dist.get("start").real(),
					  dist.get("range").real()
					  );
			printf("Created uniform distribution: start=%f range=%f\n",
			       ((Uniform*)ret)->mStart, ((Uniform*)ret)->mRange);
		}

		if (!ret) {
			throw cfgu::Exception::format("No such distribution '%s'.\n", dist_name);
		}

		return ret;
	}

	Distribution::Distribution(): 
		mRng(NULL)
	{
		static bool need_init = true;
		
		if(need_init) {
			gsl_rng_env_setup();
			need_init = false;
		}
		
		mRng = gsl_rng_alloc(gsl_rng_default);
	}
	
	Distribution::~Distribution()
	{
		gsl_rng_free(mRng);
	}
	
	Normal::Normal(double mean, double variance):
		mMean(mean), mVariance(variance)
	{
	}
	
	double Normal::generate()
	{
		/* gsl wants stddev, not variance */
		double base = gsl_ran_gaussian(mRng, sqrt(mVariance));
		
		return base + mMean;
	}
	
	Uniform::Uniform(double start, double range):
		mStart(start), mRange(range)
	{
	}
	
	double Uniform::generate()
	{
		return mStart + (gsl_rng_uniform(mRng) * mRange);
	}
};
