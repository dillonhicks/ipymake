Name:		kusp-discovery
Version:	0.9
Release:	5%{?dist}
Summary:	KUSP DISCOVERY User Tools

Group:		Development/Libraries	
License:	GPL
URL:		http://www.ittc.ku.edu/kusp
Source0:	kusp-discovery.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	cmake,flex,bison,swig,gcc,gcc-c++,kusp-common,kusp-datastreams
Requires:	python-ply gnuplot kusp-common kusp-datastreams

%description

The Discovery package for KUSP.

%prep
rm -rf %{_builddir}/kusp-discovery
%setup -q -n kusp-discovery

%build
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$RPM_BUILD_ROOT%{_prefix}  -DKERNELROOT=/usr/src/kernels/%(uname -r) -DIS_RPM_BUILD=1 -DDISCOVERY_RPM=1
make VERBOSE=1

%install
rm -rf $RPM_BUILD_ROOT
cd build
%makeinstall


%files
%defattr(-,root,root,-)
%doc
%{_bindir}/*
%{_libdir}/*
