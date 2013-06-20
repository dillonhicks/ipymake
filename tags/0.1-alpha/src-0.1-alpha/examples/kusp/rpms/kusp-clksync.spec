Name:		kusp-clksync
Version:	0.9
Release:	5%{?dist}
Summary:	KUSP CLKSYNC User Tools

Group:		Development/Libraries	
License:	GPL
URL:		http://www.ittc.ku.edu/kusp
Source0:	kusp-clksync.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	cmake,flex,bison,swig,gcc,gcc-c++,kusp-common
Requires:	python-ply gnuplot kusp-common

%description

The Clksync user tools package for KUSP.

%prep
rm -rf %{_builddir}/kusp-clksync
%setup -q -n kusp-clksync

%build
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$RPM_BUILD_ROOT%{_prefix}  -DKERNELROOT=/usr/src/kernels/%(uname -r) -DIS_RPM_BUILD=1 -DCLKSYNC_RPM=1
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

%changelog
