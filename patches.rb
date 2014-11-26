# Monkey-patching for RubyGems and Bundler to play nicely with Vagrant

# Don't touch the binary when not needed.
# https://github.com/rubygems/rubygems/pull/1057
class Gem::Installer
  def generate_bin # :nodoc:
    return if spec.executables.nil? or spec.executables.empty?

    Dir.mkdir @bin_dir unless File.exist? @bin_dir
    raise Gem::FilePermissionError.new(@bin_dir) unless File.writable? @bin_dir

    spec.executables.each do |filename|
      filename.untaint
      bin_path = File.join gem_dir, spec.bindir, filename

      unless File.exist? bin_path then
        # TODO change this to a more useful warning
        warn "#{bin_path} maybe `gem pristine #{spec.name}` will fix it?"
        next
      end

      mode = File.stat(bin_path).mode
      FileUtils.chmod mode | 0111, bin_path unless (mode | 0111) == mode

      check_executable_overwrite filename

      if @wrappers then
        generate_bin_script filename, @bin_dir
      else
        generate_bin_symlink filename, @bin_dir
      end

    end
  end
end

# Fix rubygems 2.2 compatibility
# https://github.com/bundler/bundler/pull/3237
module Bundler
  module SharedHelpers
    private
    def clean_load_path
      # handle 1.9 where system gems are always on the load path
      if defined?(::Gem)
        me = File.expand_path("../../", __FILE__)

        # RubyGems 2.2+ can put binary extension into dedicated folders,
        # therefore use RubyGems facilities to obtain their load paths.
        if Gem::Specification.method_defined? :full_require_paths
          loaded_gem_paths = Gem.loaded_specs.map do |n, s|
            s.full_require_paths.none? {|path| File.expand_path(path) =~ /^#{Regexp.escape(me)}/} ? s.full_require_paths : []
          end
          loaded_gem_paths.flatten!

          $LOAD_PATH.reject! {|p| loaded_gem_paths.delete(p) }
        else
          $LOAD_PATH.reject! do |p|
            next if File.expand_path(p) =~ /^#{Regexp.escape(me)}/
            p != File.dirname(__FILE__) &&
              Bundler.rubygems.gem_path.any?{|gp| p =~ /^#{Regexp.escape(gp)}/ }
          end
        end
        $LOAD_PATH.uniq!
      end
    end
  end
end

# Remove useless gem build step.
# https://github.com/bundler/bundler/pull/3238
module Bundler
  class Source

    class Path < Source

      private
      def generate_bin(spec, disable_extensions = false)
        gem_dir  = Pathname.new(spec.full_gem_path)

        # Some gem authors put absolute paths in their gemspec
        # and we have to save them from themselves
        spec.files = spec.files.map do |p|
          next if File.directory?(p)
          begin
            Pathname.new(p).relative_path_from(gem_dir).to_s
          rescue ArgumentError
            p
          end
        end.compact

        SharedHelpers.chdir(gem_dir) do
          installer = Path::Installer.new(spec, :env_shebang => false)
          run_hooks(:pre_install, installer)
          installer.build_extensions unless disable_extensions
          run_hooks(:post_build, installer)
          installer.generate_bin
          run_hooks(:post_install, installer)
        end
      rescue Gem::InvalidSpecificationException => e
        Bundler.ui.warn "\n#{spec.name} at #{spec.full_gem_path} did not have a valid gemspec.\n" \
                        "This prevents bundler from installing bins or native extensions, but " \
                        "that may not affect its functionality."

        if !spec.extensions.empty? && !spec.email.empty?
          Bundler.ui.warn "If you need to use this package without installing it from a gem " \
                          "repository, please contact #{spec.email} and ask them " \
                          "to modify their .gemspec so it can work with `gem build`."
        end

        Bundler.ui.warn "The validation message from Rubygems was:\n  #{e.message}"
      end
    end
  end
end
