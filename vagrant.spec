%global bashcompletion_dir %(pkg-config --variable=completionsdir bash-completion 2> /dev/null || :)
%global vagrant_dir %{_datadir}/%{name}
%global vagrant_plugin_dir %{_sharedstatedir}/%{name}

Name: vagrant
Version: 1.6.5
Release: 11%{?dist}
Summary: Build and distribute virtualized development environments
Group: Development/Languages
License: MIT
URL: http://vagrantup.com
Source0: https://github.com/mitchellh/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

# Upstream binstub with adjusted paths, the offical way how to run vagrant
Source1: binstub

Patch0: vagrant-1.6.5-fix-dependencies.patch

Requires: ruby(release)
Requires: ruby(rubygems) >= 1.3.6
# Explicitly specify MRI, since Vagrant does not work with JRuby ATM.
Requires: ruby
Requires: rubygem(bundler) >= 1.5.2
Requires: rubygem(hashicorp-checkpoint) >= 0.1.1
Requires: rubygem(childprocess) >= 0.5.0
Requires: rubygem(erubis) >= 2.7.0
Requires: rubygem(i18n) >= 0.6.0
Requires: rubygem(listen) >= 2.7.1
Requires: rubygem(log4r)
Requires: rubygem(net-ssh) >= 2.6.6
Requires: rubygem(net-scp) >= 1.1.0
Requires: bsdtar
#Requires: curl
#Requires: libffi
#Requires: libxml2
#Requires: libxslt
#Requires: libyaml
#Requires: openssl
#Requires: zlib
#Requires: ca-certificates
# libvirt as a default provider
#Requires: rubygem(vagrant-libvirt)

# Vagrant libvirt requires (just for the time beeing so that plugin
# installation from upstream gem is seemless)
#Requires: rubygem(fog) >= 1.15
#Requires: rubygem(fog) < 2
Requires: rubygem(nokogiri) >= 1.6
#Requires: rubygem(nokogiri) < 1.7
#Requires: rubygem(ruby-libvirt) >= 0.4.0
#Requires: rubygem(ruby-libvirt) < 0.5.0
#Requires: rubygem(json) = 1.8.1
#Requires: rubygem(ffi) = 1.9.3
#Requires: polkit-pkla-compat
#Requires(pre): shadow-utils

# For tests
#BuildRequires: rubygem(listen) >= 2.7.1
#BuildRequires: rubygem(childprocess) >= 0.5.0
#BuildRequires: rubygem(net-ssh) >= 2.6.6
#BuildRequires: rubygem(net-ssh) < 2.10
#BuildRequires: rubygem(net-scp) >= 1.1.0
#BuildRequires: rubygem(net-scp) < 1.2
#BuildRequires: rubygem(i18n) >= 0.6.0
#BuildRequires: rubygem(erubis) >= 2.7.0

#BuildRequires: rubygem(minitest)
#BuildRequires: rubygem(rspec)
#BuildRequires: rubygem(mocha)
#BuildRequires: rubygem(bundler)
#BuildRequires: ruby-devel
#BuildRequires: git
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


%prep
%setup -q

%patch0 -p1

#sed -i '/dependency/ d' %{name}.gemspec

# Add missing dependencies
# These needs to be part of .gemspec so Bundler works as expected
#sed -i -e "72i s\.add_dependency(\%q<json>)" %{name}.gemspec
#sed -i -e "72i s\.add_dependency(\%q<json_pure>)" %{name}.gemspec

%build

%install
mkdir -p %{buildroot}%{vagrant_dir}
cp -pa ./* \
        %{buildroot}%{vagrant_dir}/


find %{buildroot}%{vagrant_dir}/bin -type f | xargs chmod a+x

# TODO: The .gemspec search for .gitignore. May be the .gemspec should be adjusted.
touch %{buildroot}%{vagrant_dir}/.gitignore

# Provide executable similar to upstream:
# https://github.com/mitchellh/vagrant-installers/blob/master/substrate/modules/vagrant_installer/templates/vagrant.erb
install -D -m 755 %{SOURCE1} %{buildroot}%{_bindir}/vagrant
sed -i 's|@vagrant_dir@|%{vagrant_dir}|' %{buildroot}%{_bindir}/vagrant
sed -i 's|@vagrant_plugin_dir@|%{vagrant_plugin_dir}|' %{buildroot}%{_bindir}/vagrant

# auto-completion
install -D -m 0644 %{buildroot}%{vagrant_dir}/contrib/bash/completion.sh \
  %{buildroot}%{bashcompletion_dir}/%{name}

# create the global home dir
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}
#echo "{}" > %{buildroot}%{_sharedstatedir}/%{name}/plugins.json

## Fix getting the SSL cert path for the downloader
#sed -i -e "s/downloader_options\[:ca_cert\] = env\[:box_download_ca_cert\]/downloader_options\[:ca_cert\] = (env\[:box_download_ca_cert\] || ENV\['SSL_CERT_FILE'\])/" %{buildroot}%{gem_instdir}/lib/vagrant/action/builtin/box_add.rb


# libvirt as a default
#sed -i -e "s|If all else fails, return VirtualBox|If all else fails, return libvirt|" %{buildroot}%{gem_instdir}/lib/vagrant/environment.rb
#sed -i -e "s|return :virtualbox|return :libvirt|" %{buildroot}%{gem_instdir}/lib/vagrant/environment.rb

# Temporal fix for Vagrant not seeing the extensions
# Let's require them sooner
#sed -i -e "2irequire 'nokogiri'" %{buildroot}%{gem_instdir}/bin/vagrant
#sed -i -e "3irequire 'libvirt'" %{buildroot}%{gem_instdir}/bin/vagrant

#%%check
#pushd .%{gem_instdir}
#gem install log4r --version 1.1.10 -N
#gem install wdm -N
#gem install winrm -N
#gem install rb-kqueue -N
#gem install listen --version 2.7.1 -N
#gem install childprocess --version 0.5.0 -N
#bundle install
#rm -rf ./test/unit/vagrant/plugin/
#ruby -rbundler -I.:test:lib -e 'Dir.glob "test/unit/vagrant/*_test.rb", &method(:require)'
#popd

%pre
getent group vagrant >/dev/null || groupadd -r vagrant
 
%files
%{_datadir}/%{name}
%{_bindir}/%{name}
%{bashcompletion_dir}/%{name}
%dir %{_sharedstatedir}/%{name}
%ghost %{_sharedstatedir}/%{name}/plugins.json

%files doc

%changelog
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
