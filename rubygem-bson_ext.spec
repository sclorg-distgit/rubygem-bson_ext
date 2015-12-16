%{!?scl:%global pkg_name %{name}}
%{?scl:%scl_package rubygem-%{gem_name}}
%global gem_name bson_ext

%global rubyabi 1.9.1

Summary: C extensions for Ruby BSON
Name: %{?scl:%scl_prefix}rubygem-%{gem_name}
Version: 1.9.2
Release: 2.sc1%{?dist}
Group: Development/Languages
License: ASL 2.0
URL: http://www.mongodb.org/display/DOCS/BSON

Source0: http://rubygems.org/gems/%{gem_name}-%{version}.gem
# git clone https://github.com/mongodb/mongo-ruby-driver.git && cd mongo-ruby-driver && git checkout 1.9.2
# tar czvf bson_ext-1.9.2-tests.tgz test/bson
Source1: %{gem_name}-%{version}-tests.tgz
# Use old test_helper.rb, which does not have unnecessary dependencies.
Source2: https://raw.github.com/mongodb/mongo-ruby-driver/ffc598c0952a37fe81e35fe52e8aa0ce695cb1dd/test/bson/test_helper.rb
# Fix BSONTest#test_min_key failure on ARM.
# https://jira.mongodb.org/browse/RUBY-704
Patch1: rubygem-bson_ext-1.9.2-Fix-min_key-decoding-on-ARM.patch

Requires: %{?scl:%scl_prefix}rubygem(bson) >= 1.9.0
Requires: %{?scl:%scl_prefix}ruby(abi) =  %{rubyabi}
Requires: %{?scl:%scl_prefix}ruby(rubygems)
BuildRequires: %{?scl:%scl_prefix}ruby-devel
BuildRequires: %{?scl:%scl_prefix}ruby(abi) =  %{rubyabi}
BuildRequires: %{?scl:%scl_prefix}rubygems-devel
BuildRequires: %{?scl:%scl_prefix}ruby
# for tests:
BuildRequires: %{?scl:%scl_prefix}rubygem(activesupport)
BuildRequires: %{?scl:%scl_prefix}rubygem(bson) >= 1.9.0
BuildRequires: %{?scl:%scl_prefix}rubygem(json)
BuildRequires: %{?scl:%scl_prefix}rubygem(minitest)

Provides: %{?scl:%scl_prefix}rubygem(%{gem_name}) = %{version}

%description
C extensions to accelerate the Ruby BSON serialization. For more information
about BSON, see http://bsonspec.org.  For information about MongoDB, see
http://www.mongodb.org.


%package doc
Summary: Documentation for %{name}
Group: Documentation
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{name}


%prep
%{?scl:scl enable %scl - << \EOF}
gem unpack %{SOURCE0}
%setup -q -D -T -n  %{gem_name}-%{version}

gem spec %{SOURCE0} -l --ruby > %{gem_name}.gemspec

%patch1 -p1
%{?scl:EOF}

%build
mkdir -p .%{gem_dir}
%{?scl:scl enable %scl - << \EOF}
gem build %{gem_name}.gemspec

export CONFIGURE_ARGS="--with-cflags='%{optflags}'"
# gem install compiles any C extensions and installs into a directory
# We set that to be a local directory so that we can move it into the
# buildroot in %%install
gem install -V \
        --local \
        --install-dir .%{gem_dir} \
        --bindir .%{_bindir} \
        --force \
        --rdoc \
        %{gem_name}-%{version}.gem
%{?scl:EOF}


%install
mkdir -p %{buildroot}%{gem_dir}
mkdir -p %{buildroot}%{gem_extdir}/ext/%{gem_name}/%{gem_name}
cp -a .%{gem_dir}/* \
        %{buildroot}%{gem_dir}/

mv %{buildroot}%{gem_instdir}/ext/%{gem_name}/%{gem_name}/cbson.so \
  %{buildroot}%{gem_extdir}/ext/%{gem_name}/%{gem_name}

# Remove the binary extension sources and build leftovers.
rm -rf %{buildroot}%{gem_instdir}/ext


%check
pushd .%{gem_instdir}
# Extract tests.
tar xzvf %{SOURCE1}

# Move test_helper.rb into place.
cp %{SOURCE2} test/bson

# Remove the inclusion of bson (absolute path that doesn't exist) and rather require it while running ruby
sed -i "/require File.join(File.dirname(__FILE__), '..', '..', 'lib', 'bson')/d" test/bson/test_helper.rb

# Minitest does not provide asser_false.
sed -i 's/assert_false/refute/' test/bson/ordered_hash_test.rb

# String#to_bson_code is implemented in Mongo.
sed -i -r "s|('this.c.d < this.e')\.to_bson_code|BSON::Code.new\(\1\)|" test/bson/bson_test.rb

# https://jira.mongodb.org/browse/RUBY-466
%ifarch i686 %{arm}
sed -i "/^  def test_date_before_epoch$/,/^  end$/ s/^/#/" test/bson/bson_test.rb
%endif

%{?scl:scl enable %scl - << \EOF}
# StringIO is required by BSONTest#test_read_bson_document, but there is no
# point to report it upstream, since upstream switched to RSpec meanwhile.
RUBYOPT='-Iext/%{gem_name} -rbson -rstringio' testrb test/**/*_test.rb
%{?scl:EOF}
popd


%files
%dir %{gem_instdir}
%{gem_instdir}/LICENSE
%exclude %{gem_cache}
%{gem_spec}
%{gem_extdir}

%files doc
%doc %{gem_docdir}
%{gem_instdir}/VERSION
%{gem_instdir}/bson_ext.gemspec

%changelog
* Wed Nov 20 2013 Vít Ondruch <vondruch@redhat.com> - 1.9.2-2
- Properly fix ARM build.
- Import into ruby193 SCL.
  - Resolves: rhbz#1009573

* Tue Nov 19 2013 Vít Ondruch <vondruch@redhat.com> - 1.9.2-1
- Update to bson_ext 1.9.2.

* Mon Feb 04 2013 Troy Dawson <tdawson@redhat.com> - 1.8.1-2
- Fix the gem_extdir, again

* Mon Jan 14 2013 Troy Dawson <tdawson@redhat.com> - 1.8.1-1
- Updated to version 1.8.1
- Updated spec to do fedora 18+ gem packaging

* Wed Nov 14 2012 Troy Dawson <tdawson@redhat.com> - 1.5.2-8
- Fix the gem_extdir

* Sat Sep 29 2012 Troy Dawson <tdawson@redhat.com> - 1.5.2-6
- Release bump for rebuild into both i386 and x86_64

* Mon Jun 11 2012 Troy Dawson <tdawson@redhat.com> - 1.5.2-5
- Changed ruby_sitearch to be gem_extdir

* Mon Jun 11 2012 Troy Dawson <tdawson@redhat.com> - 1.5.2-4
- Changed spec file to work with scl
- Rebuilt for scl

* Fri Jan 27 2012 Troy Dawson <tdawson@redhat.com> - 1.5.2-1
- Updated to 1.5.2

* Fri Sep 23 2011 bkabrda <bkabrda@redhat.com> - 1.4.0-2
- Moved test cleanup to check section.

* Thu Sep 22 2011 Bohuslav Kabrda <bkabrda@redhat.com> - 1.4.0-1
- Version 1.4.0 (removed the fix for failing tests, as it is now in upstream).

* Tue Sep 20 2011 Bohuslav Kabrda <bkabrda@redhat.com> - 1.3.1-2
- Added the fix for failing tests on i386 (should be fixed in 1.4.0, so it can be removed then) -
  see https://github.com/mongodb/mongo-ruby-driver/commit/e613880922beaf1e80274aa183aa5ac0a9d09ac4

* Thu Sep 08 2011 Bohuslav Kabrda <bkabrda@redhat.com> - 1.3.1-1
- Initial package
