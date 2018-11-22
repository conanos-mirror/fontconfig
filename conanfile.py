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

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    

    def requirements(self):
        self.requires.add("expat/2.2.5@conanos/stable")
        self.requires.add("freetype/2.9.1@conanos/stable")

        config_scheme(self)

    def build_requirements(self):
        self.build_requires("libpng/1.6.34@conanos/stable")
        self.build_requires("bzip2/1.0.6@conanos/stable")
        self.build_requires("zlib/1.2.11@conanos/stable")
        self.build_requires("gperf/3.1@bincrafters/stable")

        if self.settings.os == "Linux":
            self.build_requires("libuuid/1.0.3@bincrafters/stable")
            

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx


    def source(self):
        src_folder = os.path.join(self.source_folder,self._source_subfolder)
        if self.settings.os == "Windows" and os.path.exists(src_folder):
            os.removedirs(src_folder)

        url_ = "https://github.com/CentricularK/fontconfig.git"
        branch_ = "testing/2.13.0"
        git = tools.Git(folder=self._source_subfolder)
        git.clone(url_, branch=branch_)

    def build(self):
        pkg_config_paths=[os.path.join(self.deps_cpp_info["freetype"].rootpath, "lib", "pkgconfig"),
                          os.path.join(self.deps_cpp_info["expat"].rootpath, "lib", "pkgconfig")]
        prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
        meson = Meson(self)

        if self.settings.os == "Windows":
            libpng = [ os.path.join(self.deps_cpp_info["libpng"].rootpath, i) for i in ["lib", "bin"] ]
            bzip2 = [ os.path.join(self.deps_cpp_info["bzip2"].rootpath, i) for i in ["lib", "bin"] ]
            zlib = [ os.path.join(self.deps_cpp_info["zlib"].rootpath, i) for i in ["lib", "bin"] ]
            expat = [ os.path.join(self.deps_cpp_info["expat"].rootpath, i) for i in ["lib", "bin"] ]
            freetype = os.path.join(self.deps_cpp_info["freetype"].rootpath, "bin")

            with tools.environment_append({ 'LIB' : os.pathsep.join([libpng[0], bzip2[0], zlib[0], expat[0], os.getenv('LIB')]),
                'PATH' : os.pathsep.join([os.path.join(prefix,"bin"),freetype,zlib[1],bzip2[1],libpng[1],expat[1],os.getenv('PATH')])}):
                meson.configure(defs={'prefix' : prefix},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

        if self.settings.os == "Linux":
            pkg_config_paths.extend([os.path.join(self.deps_cpp_info["zlib"].rootpath, "lib", "pkgconfig"),
                                     os.path.join(self.deps_cpp_info["bzip2"].rootpath, "lib", "pkgconfig"),
                                     os.path.join(self.deps_cpp_info["libpng"].rootpath, "lib", "pkgconfig"),
                                     os.path.join(self.deps_cpp_info["libuuid"].rootpath, "lib", "pkgconfig"),])
            path = [os.path.join(self.deps_cpp_info["gperf"].rootpath, "bin")]
            include = [os.path.join(self.deps_cpp_info["libuuid"].rootpath, "include")]
            libpath = [os.path.join(self.deps_cpp_info["freetype"].rootpath, "lib"),
                       os.path.join(self.deps_cpp_info["bzip2"].rootpath, "lib"),
                       os.path.join(self.deps_cpp_info["zlib"].rootpath, "lib"),
                       os.path.join(self.deps_cpp_info["libpng"].rootpath, "lib"),]
            with tools.environment_append({
                'PATH' : os.pathsep.join(path+[os.getenv('PATH')]),
                'C_INCLUDE_PATH' : os.pathsep.join(include),
                'LD_LIBRARY_PATH' : os.pathsep.join(libpath),
                }):
                meson.configure(defs={'prefix' : prefix, 'libdir':'lib'},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

