from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from shutil import copyfile
import os


class FontconfigConan(ConanFile):
    name = "fontconfig"
    version = "2.12.6"
    description = "Fontconfig is a library for configuring and customizing font access."
    url = "https://github.com/conanos/fontconfig"
    homepage = "https://www.freedesktop.org/wiki/Software/fontconfig/"
    license = "MIT"
    exports = ["COPYING"]
    generators = "cmake"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    requires = "expat/2.2.5@conanos/dev","freetype/2.9.0@conanos/dev","zlib/1.2.11@conanos/dev", "bzip2/1.0.6@conanos/dev","libpng/1.6.34@conanos/dev"

    source_subfolder = "source_subfolder"

    def source(self):
        url_ = 'https://www.freedesktop.org/software/fontconfig/release/fontconfig-{version}.tar.gz'.format(version=self.version)
        tools.get(url_)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            if tools.os_info.is_linux:
                with tools.environment_append({
                    #'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
                    #%(self.deps_cpp_info["expat"].rootpath,self.deps_cpp_info["freetype"].rootpath,
                    #self.deps_cpp_info["zlib"].rootpath,self.deps_cpp_info["bzip2"].rootpath,self.deps_cpp_info["libpng"].rootpath,),
                    'LIBRARY_PATH' : '%s/lib:%s/lib'
                    %(self.deps_cpp_info["bzip2"].rootpath,self.deps_cpp_info["libpng"].rootpath),
                    'LD_LIBRARY_PATH' : '%s/lib:%s/lib'
                    %(self.deps_cpp_info["bzip2"].rootpath,self.deps_cpp_info["freetype"].rootpath)
                    }):
                    
                    self.run('autoreconf -f -i')
                    autotools = AutoToolsBuildEnvironment(self)
                    _args = ["--prefix=%s/builddir/install"%(os.getcwd()),"--disable-silent-rules","--disable-docs"]
                    if self.options.shared:
                        _args.extend(['--enable-shared=yes','--enable-static=no'])
                    else:
                        _args.extend(['--enable-shared=no','--enable-static=yes'])
                    autotools.configure(args=_args,
                                        pkg_config_paths=["%s/lib/pkgconfig"%(self.deps_cpp_info["expat"].rootpath),
                                                          "%s/lib/pkgconfig"%(self.deps_cpp_info["freetype"].rootpath),
                                                          "%s/lib/pkgconfig"%(self.deps_cpp_info["zlib"].rootpath),
                                                          "%s/lib/pkgconfig"%(self.deps_cpp_info["bzip2"].rootpath),
                                                          "%s/lib/pkgconfig"%(self.deps_cpp_info["libpng"].rootpath),])
                    autotools.make(args=["-j2"])
                    autotools.install()


    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir/install"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

