from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from shutil import copyfile
import os
from conanos.build import config_scheme
from conans import Meson


class FontconfigConan(ConanFile):
    name = "fontconfig"
    version = "2.13.0"
    description = "Fontconfig is a library for configuring and customizing font access."
    url = "https://github.com/CentricularK/fontconfig"
    homepage = "https://www.freedesktop.org/wiki/Software/fontconfig/"
    license = "MIT"
    exports = ["COPYING"]
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = { 'shared': False, 'fPIC': True }
    #requires = "expat/2.2.5@conanos/dev","freetype/2.9.0@conanos/dev","zlib/1.2.11@conanos/dev", "bzip2/1.0.6@conanos/dev","libpng/1.6.34@conanos/dev"

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    

    def requirements(self):
        self.requires.add("expat/2.2.5@conanos/stable")
        self.requires.add("freetype/2.9.1@conanos/stable")

        config_scheme(self)

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("libpng/1.6.34@conanos/stable")
            self.build_requires("bzip2/1.0.6@conanos/stable")
            self.build_requires("zlib/1.2.11@conanos/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx


    def source(self):
        if self.settings.os == 'Linux':
            url_ = 'https://www.freedesktop.org/software/fontconfig/release/fontconfig-{version}.tar.gz'.format(version=self.version)
            tools.get(url_)
            extracted_dir = self.name + "-" + self.version
            os.rename(extracted_dir, self._source_subfolder)
        
        if self.settings.os == "Windows":
            url_ = "https://github.com/CentricularK/fontconfig.git"
            branch_ = "testing/2.13.0"
            git = tools.Git(folder=self._source_subfolder)
            git.clone(url_, branch=branch_)

    def build(self):
        if self.settings.os == 'Linux':
            with tools.chdir(self._source_subfolder):
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

        if self.settings.os == "Windows":
            meson = Meson(self)
            libpng = [ os.path.join(self.deps_cpp_info["libpng"].rootpath, i) for i in ["lib", "bin"] ]
            bzip2 = [ os.path.join(self.deps_cpp_info["bzip2"].rootpath, i) for i in ["lib", "bin"] ]
            zlib = [ os.path.join(self.deps_cpp_info["zlib"].rootpath, i) for i in ["lib", "bin"] ]
            expat = [ os.path.join(self.deps_cpp_info["expat"].rootpath, i) for i in ["lib", "bin"] ]
            freetype = os.path.join(self.deps_cpp_info["freetype"].rootpath, "bin")
            prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
            with tools.environment_append({ 'LIB' : os.pathsep.join([libpng[0], bzip2[0], zlib[0], expat[0], os.getenv('LIB')]),
                'PATH' : os.pathsep.join([os.path.join(prefix,"bin"),freetype,zlib[1],bzip2[1],libpng[1],expat[1],os.getenv('PATH')])}):
                meson.configure(defs={'prefix' : prefix},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=[os.path.join(self.deps_cpp_info["freetype"].rootpath, "lib", "pkgconfig"),
                                                  os.path.join(self.deps_cpp_info["expat"].rootpath, "lib", "pkgconfig")])
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self._source_subfolder):
                self.copy("*", src="%s/builddir/install"%(os.getcwd()))
        
        if tools.os_info.is_windows:
            self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))


    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

