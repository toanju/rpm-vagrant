%global bashcompletion_dir %(pkg-config --variable=completionsdir bash-completion 2> /dev/null || :)

%global vagrant_spec_commit c0dafc996165bf1628b672dd533f1858ff66fe4a

Name: vagrant
Version: 1.6.5
Release: 13%{?dist}
Summary: Build and distribute virtualized development environments
Group: Development/Languages
License: MIT
URL: http://vagrantup.com
Source0: https://github.com/mitchellh/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

# Upstream binstub with adjusted paths, the offical way how to run vagrant
Source1: binstub

# The library has no official release yet. But since it is just test
# dependency, it should be fine to include the source right here.
Source2: https://github.com/mitchellh/%{name}-spec/archive/%{vagrant_spec_commit}/%{name}-spec-%{vagrant_spec_commit}.tar.gz

# Monkey-patching needed for Vagrant to work until the respective patches
# for RubyGems and Bundler are in place
Source3: patches.rb

Source4: macros.vagrant

# The load directive is supported since RPM 4.12, i.e. F21+. The build process
# fails on older Fedoras.
%{?load:%{SOURCE4}}

Patch0: vagrant-1.6.5-fix-dependencies.patch

Requires: ruby(release)
Requires: ruby(rubygems) >= 1.3.6
# Explicitly specify MRI, since Vagrant does not work with JRuby ATM.
Requires: ruby
# rb-inotify should be installed by listen, but this dependency was removed
# in Fedora's package.
Requires: rubygem(rb-inotify)
Requires: rubygem(bundler) >= 1.5.2
Requires: rubygem(hashicorp-checkpoint) >= 0.1.1
Requires: rubygem(childprocess) >= 0.5.0
Requires: rubygem(erubis) >= 2.7.0
Requires: rubygem(i18n) >= 0.6.0
Requires: rubygem(listen) >= 2.7.1
Requires: rubygem(log4r)
Requires: rubygem(net-ssh) >= 2.6.6
Requires: rubygem(net-scp) >= 1.1.0
Requires: rubygem(nokogiri) >= 1.6
Requires: bsdtar
Requires: curl

Requires(pre): shadow-utils

BuildRequires: bsdtar
BuildRequires: rubygem(listen)
BuildRequires: rubygem(childprocess)
BuildRequires: rubygem(hashicorp-checkpoint)
BuildRequires: rubygem(log4r)
BuildRequires: rubygem(net-ssh)
BuildRequires: rubygem(net-scp)
BuildRequires: rubygem(nokogiri)
BuildRequires: rubygem(i18n)
BuildRequires: rubygem(erubis)
BuildRequires: rubygem(rb-inotify)
BuildRequires: rubygem(rspec) < 3
BuildRequires: rubygem(bundler)
BuildRequires: pkgconfig(bash-completion)
BuildArch: noarch

%description
Vagrant is a tool for building and distributing virtualized development
environments.

%package doc
Summary: Documentation for %{name}
Group: Documentation
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{name}.

%package devel
Summary: Package shipping development files for Vagrant

%description devel
Package shipping macros for convinient plugin registration and
unregistration.

%prep
%setup -q

%patch0 -p1

%build

%install
mkdir -p %{buildroot}%{vagrant_dir}
cp -pa ./* \
        %{buildroot}%{vagrant_dir}/

find %{buildroot}%{vagrant_dir}/bin -type f | xargs chmod a+x

rm %{buildroot}%{vagrant_dir}/{CHANGELOG,CONTRIBUTING,README}.md
rm %{buildroot}%{vagrant_dir}/LICENSE

# Provide executable similar to upstream:
# https://github.com/mitchellh/vagrant-installers/blob/master/substrate/modules/vagrant_installer/templates/vagrant.erb
install -D -m 755 %{SOURCE1} %{buildroot}%{_bindir}/vagrant
sed -i 's|@vagrant_dir@|%{vagrant_dir}|' %{buildroot}%{_bindir}/vagrant
sed -i 's|@vagrant_plugin_conf_dir@|%{vagrant_plugin_conf_dir}|' %{buildroot}%{_bindir}/vagrant

# auto-completion
install -D -m 0644 %{buildroot}%{vagrant_dir}/contrib/bash/completion.sh \
  %{buildroot}%{bashcompletion_dir}/%{name}

# create the global home dir
install -d -m 755 %{buildroot}%{vagrant_plugin_conf_dir}

# Install the monkey-patch file and load it from Vagrant after loading RubyGems
cp %{SOURCE3}  %{buildroot}%{vagrant_dir}/lib/vagrant
sed -i -e "11irequire 'vagrant/patches'" %{buildroot}%{vagrant_dir}/lib/vagrant.rb

# Install Vagrant macros
mkdir -p %{buildroot}%{_rpmconfigdir}/macros.d/
cp %{SOURCE4} %{buildroot}%{_rpmconfigdir}/macros.d/
sed -i "s/%%{name}/%{name}/" %{buildroot}%{_rpmconfigdir}/macros.d/macros.%{name}


%check
# Unpack the vagran-spec and adjust the directory name.
tar xvzf %{S:2} -C ..
mv ../vagrant-spec{-%{vagrant_spec_commit},}

# Remove the git reference, which is useless in our case.
sed -i '/git/ s/^/#/' ../vagrant-spec/vagrant-spec.gemspec

# TODO: winrm is not in Fedora yet.
rm -rf test/unit/plugins/communicators/winrm
sed -i '/it "eager loads WinRM" do/,/^      end$/ s/^/#/' test/unit/vagrant/machine_test.rb
sed -i '/it "should return the specified communicator if given" do/,/^    end$/ s/^/#/' test/unit/vagrant/machine_test.rb

bundle --local

# Test suite must be executed in order.
ruby -rbundler/setup -I.:lib -e 'Dir.glob("test/unit/**/*_test.rb").sort.each &method(:require)'

%pre
getent group vagrant >/dev/null || groupadd -r vagrant
 
%files
%license LICENSE
%{_bindir}/%{name}
%dir %{vagrant_dir}
%exclude %{vagrant_dir}/.*
%exclude %{vagrant_dir}/Vagrantfile
%{vagrant_dir}/bin
# TODO: Make more use of contribs.
%{vagrant_dir}/contrib
%exclude %{vagrant_dir}/contrib/bash
%{vagrant_dir}/vagrant.gemspec
%{vagrant_dir}/keys
%{vagrant_dir}/lib
%{vagrant_dir}/plugins
%exclude %{vagrant_dir}/scripts
%{vagrant_dir}/templates
%{vagrant_dir}/version.txt
%exclude %{vagrant_dir}/website
%{bashcompletion_dir}/%{name}
%dir %{_sharedstatedir}/%{name}
%ghost %{_sharedstatedir}/%{name}/plugins.json

%files doc
%doc CONTRIBUTING.md CHANGELOG.md README.md
%{vagrant_dir}/Gemfile
%{vagrant_dir}/Rakefile
%{vagrant_dir}/tasks
%{vagrant_dir}/test
%{vagrant_dir}/vagrant-spec.config.example.rb

%files devel
%{_rpmconfigdir}/macros.d/macros.%{name}


%changelog
* Tue Nov 25 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-13
- Create -devel sub-package

* Mon Nov 24 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-12
- Include monkey-patching for RubyGems and Bundler for now

* Wed Oct 22 2014 Vít Ondruch <vondruch@redhat.com> - 1.6.5-11
- Make vagrant non-rubygem package.

* Tue Oct 14 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-10
- rebuilt

* Tue Oct 07 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-9
- Register vagrant-libvirt automatically

* Tue Sep 30 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-8
- Set libvirt as a default provider

* Tue Sep 23 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-7
- Require core dependencies for vagrant-libvirt beforehand

* Mon Sep 22 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-6
- Fix SSL cert path for the downloader

* Tue Sep 16 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-5
- rebuilt

* Tue Sep 16 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-4
- rebuilt

* Sat Sep 13 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-3
- Include libvirt requires for now

* Wed Sep 10 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-2
- Add missing deps on Bundler and hashicorp-checkpoint

* Mon Sep 08 2014 Josef Stribny <jstribny@redhat.com> - 1.6.5-1
* Update to 1.6.5

* Mon Sep 08 2014 Josef Stribny <jstribny@redhat.com> - 1.6.3-2
- Clean up
- Update to 1.6.3

* Fri Oct 18 2013  <adrahon@redhat.com> - 1.3.3-1.1
- Misc bug fixes, no separate package for docs, /etc/vagrant management

* Tue Sep 24 2013  <adrahon@redhat.com> - 1.3.3-1
- Initial package
