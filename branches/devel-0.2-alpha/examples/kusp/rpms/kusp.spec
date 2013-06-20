Name:		kusp
Version:	0.9
Release:	5%{?dist}
Summary:	This is KUSP

Group:		Development/Libraries	
License:	GPL
URL:		http://www.ittc.ku.edu/kusp
Source0:	kusp.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Provides:       kusp-common,kusp-datastreams,kusp-gsched,kusp-ccsm,kusp-discovery,kusp-clksync,kusp-netspec
BuildRequires:	cmake,flex,bison,swig,gcc,gcc-c++
Requires:	python-ply gnuplot

%description

KUSP User Level Software. This release includes the KUSP subsystems:
clksync, CCSM (Computation Component Set Manager), Data Streams,
Discovery, Group Scheduling, KUSP Common Components, and NetSpec. The
subsystems provide tools for interacting with the KUSP Kernel as will
as standalone application that can be used regardless if the KUSP
Kernel is installed.


%prep
rm -rf %{_builddir}/kusp
%setup -q -n kusp

%build
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$RPM_BUILD_ROOT%{_prefix}  -DKERNELROOT=$KUSPKERNELROOT -DIS_RPM_BUILD=1
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
%{_includedir}/*
%{_datadir}/*
