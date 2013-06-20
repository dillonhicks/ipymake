#ifndef RDIST_HPP
#define RDIST_HPP
#include <cstdio>
#include <gsl/gsl_rng.h>
#include "cfgu.h"

namespace rdist
{

	class Distribution
	{
	public:
		virtual double generate() = 0;
		virtual ~Distribution();
	protected:
		Distribution();
		gsl_rng* mRng;
	};

	class Normal: public Distribution
	{
	public:
		Normal(double mean, double variance);
		double generate();
	public:
		double mMean;
		double mVariance;
	};

	class Uniform: public Distribution
	{
	public:
		Uniform(double start, double range);
		double generate();
	public:
		double mStart;
		double mRange;
	};

	Distribution* config(cfgu::Object dist);

};

#endif

