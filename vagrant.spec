%global bashcompletion_dir %(pkg-config --variable=completionsdir bash-completion 2> /dev/null || :)

%global vagrant_spec_commit 9bba7e1228379c0a249a06ce76ba8ea7d276afbe

Name: vagrant
Version: 1.9.1
Release: 1%{?dist}
Summary: Build and distribute virtualized development environments
Group: Development/Languages
License: MIT
URL: http://vagrantup.com
Source0: https://github.com/mitchellh/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz
# Upstream binstub with adjusted paths, the offical way how to run vagrant
Source1: binstub
# The library has no official release yet. But since it is just test
# dependency, it should be fine to include the source right here.
# wget https://github.com/mitchellh/vagrant-spec/archive/9bba7e1228379c0a249a06ce76ba8ea7d276afbe/vagrant-spec-9bba7e1228379c0a249a06ce76ba8ea7d276afbe.tar.gz
Source2: https://github.com/mitchellh/%{name}-spec/archive/%{vagrant_spec_commit}/%{name}-spec-%{vagrant_spec_commit}.tar.gz
# Monkey-patching needed for Vagrant to work until the respective patches
# for RubyGems and Bundler are in place
Source4: macros.vagrant

# The load directive is supported since RPM 4.12, i.e. F21+. The build process
# fails on older Fedoras.
%{?load:%{SOURCE4}}

Patch0: vagrant-1.9.1-fix-dependencies.patch

# Disable ansible winrm tests 
Patch1: vagrant-1.8.1-disable-winrm-tests.patch

Requires: ruby(release)
Requires: ruby(rubygems) >= 1.3.6
# Explicitly specify MRI, since Vagrant does not work with JRuby ATM.
Requires: ruby
Requires: rubygem(hashicorp-checkpoint) >= 0.1.1
Requires: rubygem(hashicorp-checkpoint) < 0.2
Requires: rubygem(childprocess) >= 0.5.0
Requires: rubygem(childprocess) < 0.6
Requires: rubygem(erubis) >= 2.7.0
Requires: rubygem(erubis) < 2.8
Requires: rubygem(i18n) >= 0.6.0
Requires: rubygem(i18n) <= 0.8.0
Requires: rubygem(json)
Requires: rubygem(listen) >= 3.1.5
Requires: rubygem(listen) < 3.2
Requires: rubygem(log4r) >= 1.1.9
Requires: rubygem(log4r) < 1.1.11
Requires: rubygem(net-ssh) >= 3.0
Requires: rubygem(net-ssh) < 4
Requires: rubygem(net-scp) >= 1.1.0
Requires: rubygem(nokogiri) >= 1.6
Requires: rubygem(net-sftp) >= 2.1
Requires: rubygem(net-sftp) < 3
Requires: rubygem(rest-client) < 3.0
Requires: bsdtar
Requires: curl

Recommends: vagrant(vagrant-libvirt)

Requires(pre): shadow-utils

BuildRequires: bsdtar
BuildRequires: ruby
BuildRequires: rubygem(listen)
BuildRequires: rubygem(childprocess)
BuildRequires: rubygem(hashicorp-checkpoint)
BuildRequires: rubygem(log4r)
BuildRequires: rubygem(net-ssh)
BuildRequires: rubygem(net-scp)
BuildRequires: rubygem(nokogiri)
BuildRequires: rubygem(i18n)
BuildRequires: rubygem(json)
BuildRequires: rubygem(erubis)
BuildRequires: rubygem(rspec) < 3
BuildRequires: rubygem(net-sftp)
BuildRequires: rubygem(rest-client)
BuildRequires: rubygem(thor)
BuildRequires: rubygem(webmock)
BuildRequires: rubygem(fake_ftp)
BuildRequires: pkgconfig(bash-completion)
BuildArch: noarch

# Since Vagrant itself is installed on the same place as its plugins
# the vagrant_plugin macros can be reused in the spec file, but the plugin
# name must be specified.
%global vagrant_plugin_name vagrant

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
%setup -q -b2

%patch0 -p1
%patch1 -p1

%build
gem build %{name}.gemspec

gem install -V --local --install-dir .%{vagrant_plugin_dir} \
  --ignore-dependencies --force --no-document --backtrace \
  %{name}-%{version}.gem


%install
mkdir -p %{buildroot}%{vagrant_plugin_dir}
cp -pa .%{vagrant_plugin_dir}/* \
        %{buildroot}%{vagrant_plugin_dir}/

find %{buildroot}%{vagrant_plugin_dir}/bin -type f | xargs chmod a+x

# Provide executable similar to upstream:
# https://github.com/mitchellh/vagrant-installers/blob/master/substrate/modules/vagrant_installer/templates/vagrant.erb
install -D -m 755 %{SOURCE1} %{buildroot}%{_bindir}/vagrant
sed -i 's|@vagrant_embedded_dir@|%{vagrant_embedded_dir}|' %{buildroot}%{_bindir}/vagrant

# auto-completion
install -D -m 0644 %{buildroot}%{vagrant_plugin_instdir}/contrib/bash/completion.sh \
  %{buildroot}%{bashcompletion_dir}/%{name}
sed -i '/#!\// d' %{buildroot}%{bashcompletion_dir}/%{name}


# Install Vagrant macros
mkdir -p %{buildroot}%{_rpmconfigdir}/macros.d/
cp %{SOURCE4} %{buildroot}%{_rpmconfigdir}/macros.d/
# Expand some basic macros.
sed -i "s/%%{name}/%{name}/" \
  %{buildroot}%{_rpmconfigdir}/macros.d/macros.%{name}
sed -i "/vagrant_embedded_dir/ s/%%{name}/%{name}/" \
  %{buildroot}%{_rpmconfigdir}/macros.d/macros.%{name}
sed -i "/vagrant_embedded_dir/ s/%%{version}/%{version}/" \
  %{buildroot}%{_rpmconfigdir}/macros.d/macros.%{name}

# Create configuration directory.
install -d -m 755 %{buildroot}%{vagrant_plugin_conf_dir}
# Make sure the plugins.json exists and provide the link to
# VAGRANT_INSTALLER_EMBEDDED_DIR so Vagrant can locate the file.
touch %{buildroot}%{vagrant_plugin_conf}
ln -s -t %{buildroot}%{vagrant_embedded_dir}/ %{vagrant_plugin_conf}

# !!! Backward compatibility hack, introduced in F26 timeframe !!!
# It allows to (un)register old Vagrant plugins via newer Vagrant.
# This should be possible to remove at F29, when there is chance everybody is
# using more recent versions of Vagrant.
install -d -m 755 %{buildroot}%{vagrant_embedded_dir}/lib/vagrant/plugin
cat > %{buildroot}%{vagrant_embedded_dir}/lib/vagrant/plugin/manager.rb << 'EOF'
$LOAD_PATH.shift
$LOAD_PATH.unshift '%{vagrant_dir}/lib'
require 'vagrant/plugin/manager'
EOF


%check
# Adjust the vagrant-spec directory name.
rm -rf ../vagrant-spec
mv ../vagrant-spec{-%{vagrant_spec_commit},}

# Remove the git reference, which is useless in our case.
sed -i '/git/ s/^/#/' ../vagrant-spec/vagrant-spec.gemspec

# Relax the thor dependency, since Fedora ships with newer version.
sed -i '/thor/ s/~>/>=/' ../vagrant-spec/vagrant-spec.gemspec

#Insert new test dependencies
sed -i '25 i\  spec.add_dependency "webmock"' ../vagrant-spec/vagrant-spec.gemspec
sed -i '26 i\  spec.add_dependency "fake_ftp"' ../vagrant-spec/vagrant-spec.gemspec

# TODO: winrm is not in Fedora yet.
rm -rf test/unit/plugins/communicators/winrm
sed -i '/it "eager loads WinRM" do/,/^      end$/ s/^/#/' test/unit/vagrant/machine_test.rb
sed -i '/it "should return the specified communicator if given" do/,/^    end$/ s/^/#/' test/unit/vagrant/machine_test.rb

# Test suite must be executed in order.
ruby -I.:lib -e 'Dir.glob("test/unit/**/*_test.rb").sort.each &method(:require)'

%pre
getent group vagrant >/dev/null || groupadd -r vagrant

%post -p %{_bindir}/ruby
begin
  $LOAD_PATH.unshift "%{vagrant_dir}/lib"
  begin
    require "vagrant/plugin/manager"
  rescue LoadError => e
    raise
  end;

  unless File.exist?("%{vagrant_plugin_conf}")
    Vagrant::Plugin::StateFile.new(Pathname.new(File.expand_path "%{vagrant_plugin_conf}")).save!
  end
rescue => e
  puts "Vagrant plugin.json is not properly initialized: #{e}"
end
 
%files
# Explicitly include Vagrant plugins directory strucure to avoid accidentally
# packaged content.
%dir %{vagrant_embedded_dir}
%dir %{vagrant_plugin_dir}
%dir %{vagrant_plugin_dir}/bin
%dir %{vagrant_plugin_dir}/build_info
%dir %{dirname:%{vagrant_plugin_cache}}
%dir %{dirname:%{vagrant_plugin_docdir}}
%dir %{vagrant_plugin_dir}/extensions
%dir %{dirname:%{vagrant_plugin_instdir}}
%dir %{dirname:%{vagrant_plugin_spec}}

# Kept for backward compatibility.
%{vagrant_embedded_dir}/lib

%{_bindir}/%{name}
%dir %{vagrant_plugin_instdir}
%license %{vagrant_plugin_instdir}/LICENSE
%doc %{vagrant_plugin_instdir}/README.md
%{vagrant_plugin_dir}/bin/vagrant
%exclude %{vagrant_plugin_instdir}/.*
%exclude %{vagrant_plugin_instdir}/Vagrantfile
%{vagrant_plugin_instdir}/bin
# TODO: Make more use of contribs.
%{vagrant_plugin_instdir}/contrib
%exclude %{vagrant_plugin_instdir}/contrib/bash
# This is not the original .gemspec.
%exclude %{vagrant_plugin_instdir}/vagrant.gemspec
%{vagrant_plugin_instdir}/keys
%{vagrant_plugin_instdir}/lib
%{vagrant_plugin_instdir}/plugins
%exclude %{vagrant_plugin_instdir}/scripts
%{vagrant_plugin_instdir}/templates
%{vagrant_plugin_instdir}/version.txt
%exclude %{vagrant_plugin_cache}
%{vagrant_plugin_spec}
# TODO: This is suboptimal and may break, but can't see much better way ...
%dir %{dirname:%{bashcompletion_dir}}
%dir %{bashcompletion_dir}
%{bashcompletion_dir}/%{name}
%{vagrant_embedded_dir}/plugins.json
%dir %{vagrant_plugin_conf_dir}
%ghost %{vagrant_plugin_conf}
%{_rpmconfigdir}/macros.d/macros.%{name}

%files doc
%doc %{vagrant_plugin_instdir}/RELEASE.md
%doc %{vagrant_plugin_instdir}/CHANGELOG.md
%{vagrant_plugin_instdir}/Gemfile
%{vagrant_plugin_instdir}/Rakefile
%{vagrant_plugin_instdir}/tasks
%{vagrant_plugin_instdir}/test
%{vagrant_plugin_instdir}/vagrant-spec.config.example.rb


%changelog
* Mon Feb 13 2017 Vít Ondruch <vondruch@redhat.com> - 1.9.1-1
- Update to Vagrant 1.9.1.

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Nov 15 2016 Vít Ondruch <vondruch@redhat.com> - 1.8.7-1
- Update to Vagrant 1.8.7.

* Mon Oct 10 2016 Vít Ondruch <vondruch@redhat.com> - 1.8.6-1
- Update to Vagrant 1.8.6.

* Fri Jul 29 2016 Vít Ondruch <vondruch@redhat.com> - 1.8.5-1
- Update to Vagrant 1.8.5.

* Mon Jul 18 2016 Jun Aruga <jaruga@redhat.com> - 1.8.1-3
- Support rest-client 2.x (rhbz#1356650).

* Mon May 02 2016 Vít Ondruch <vondruch@redhat.com> - 1.8.1-2
- Fix plugin installation error (rhbz#1330208).

* Tue Feb 09 2016 Tomas Hrcka <thrcka@redhat.com> - 1.8.1-1
- New upstream release
- Disable tests using winrm

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.4-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Feb 01 2016 Vít Ondruch <vondruch@redhat.com> - 1.7.4-5
- Use another way how to make the documentation to generate.

* Mon Feb 01 2016 Vít Ondruch <vondruch@redhat.com> - 1.7.4-4
- Update the macros to keep them in sync with rubygems package.

* Wed Oct 14 2015 Josef Stribny <jstribny@redhat.com> - 1.7.4-3
- Fix: Don't use biosdevname if missing in Fedora guest

* Tue Oct 13 2015 Vít Ondruch <vondruch@redhat.com> - 1.7.4-2
- Fix Bundler 1.10.6 compatibility.
- Recommends vagrant-libvirt installation by default.

* Thu Aug 20 2015 Josef Stribny <jstribny@redhat.com> - 1.7.4-1
- Update to 1.7.4
- Patch: install plugins in isolation

* Fri Jul 10 2015 Dan Williams <dcbw@redhat.com> - 1.7.2-9
- Allow matching interfaces on MAC address

* Tue Jun 30 2015 Josef Stribny <jstribny@redhat.com> - 1.7.2-8
- Fix NFS on Fedora

* Tue Jun 16 2015 Josef Stribny <jstribny@redhat.com> - 1.7.2-7
- Fix: Remove docker0 from guest network interface enumeration

* Thu May 21 2015 Josef Stribny <jstribny@redhat.com> - 1.7.2-6
- Fix: Support new Fedora releases
- Fix: Don't try to use biosdevname if it's not installed

* Wed May 06 2015 Josef Stribny <jstribny@redhat.com> - 1.7.2-5
- Export GEM_HOME based on VAGRANT_HOME

* Tue May 05 2015 Josef Stribny <jstribny@redhat.com> - 1.7.2-4
- Include $USER path in binstub

* Fri Feb 20 2015 Vít Ondruch <vondruch@redhat.com> - 1.7.2-3
- Fix Puppet provisioning error available in 1.7.2 re-release.

* Fri Feb 20 2015 Michael Adam <madam@redhat.com> - 1.7.2-2
- Add missing dependencies.

* Thu Feb 12 2015 Tomas Hrcka <thrcka@redhat.com> - 1.7.2-1
- Update to latest upstream version 1.7.2
- Backport dependencies fix patch
- Remove permissions fix on mkdir.rb

* Mon Jan 26 2015 Vít Ondruch <vondruch@redhat.com> - 1.6.5-18
- Prepare and own plugin directory structure.

* Thu Jan 22 2015 Michael Adam <madam@redhat.com> - 1.6.5-17
- Fix %%check in an unclean build environment.
- Fix typo.

* Tue Jan 20 2015 Vít Ondruch <vondruch@redhat.com> - 1.6.5-16
- Minor review fixes.

* Tue Dec 23 2014 Vít Ondruch <vondruch@redhat.com> - 1.6.5-15
- Relax thor dependency to keep up with Fedora.

* Wed Nov 26 2014 Vít Ondruch <vondruch@redhat.com> - 1.6.5-14
- Drop -devel sub-package.

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
