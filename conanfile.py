from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration

required_conan_version = ">=1.33.0"


class VxlConan(ConanFile):
    name = "vxl"
    description = "VXL (the Vision-something-Libraries) is a collection of C++ " \
                  "libraries designed for computer vision research and implementation."
    license = "BSD-3-Clause"
    topics = ("vxl", "computer-vision", "image", "video", "classification", "topology")
    homepage = "https://vxl.github.io"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "core_numerics": [True, False],
        "core_geometry": [True, False],
        "core_serialisation": [True, False],
        "core_utilities": [True, False],
        "core_imaging": [True, False],
        "core_probability": [True, False],
        "core_video": [True, False],
        "gui": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "core_numerics": True,
        "core_geometry": True,
        "core_serialisation": True,
        "core_utilities": True,
        "core_imaging": True,
        "core_probability": True,
        "core_video": False,
        "gui": False,
    }

    exports_sources = "CMakeLists.txt", "patches/**"
    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        if self.options.core_geometry:
            self.requires("clipper/6.4.2")
        if self.options.core_imaging:
            self.requires("bzip2/1.0.8")
            self.requires("dcmtk/3.6.6")
            self.requires("libgeotiff/1.6.0")
            self.requires("libjpeg/9d")
            self.requires("libpng/1.6.37")
            self.requires("libtiff/4.2.0")
            self.requires("openjpeg/2.4.0")
            self.requires("zlib/1.2.11")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 11)

        if self.options.core_probability and not self.options.core_numerics:
            raise ConanInvalidConfiguration("core_probability requires core_numerics")
        if self.options.gui and not (self.options.core_numerics and self.options.core_geometry and \
           self.options.core_serialisation and self.options.core_utilities and self.options.core_imaging):
            raise ConanInvalidConfiguration("gui requires core_numerics, core_geometry, core_serialisation, core_utilities and core_imaging")
        if self.options.core_video and not (self.options.core_utilities and self.options.core_imaging):
            raise ConanInvalidConfiguration("core_video requires core_utilities and core_imaging")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

    def _patch_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)

        # root CMakeLists.txt
        self._cmake.definitions["VXL_LEGACY_FUTURE_REMOVE"] = True
        self._cmake.definitions["VXL_USE_HISTORICAL_IMPLICIT_CONVERSIONS"] = True
        self._cmake.definitions["VXL_USE_HISTORICAL_PROTECTED_IVARS"] = True
        if self.settings.os == "Windows":
            self._cmake.definitions["VXL_USE_WIN_WCHAR_T"] = True
        else:
            self._cmake.definitions["VXL_BUILD_POSITION_DEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        self._cmake.definitions["VXL_USE_LFS"] = False
        self._cmake.definitions["VXL_BUILD_CORE_NUMERICS_ONLY"] = False
        self._cmake.definitions["VXL_BUILD_CORE_NUMERICS"] = self.options.core_numerics
        self._cmake.definitions["VXL_BUILD_CORE_GEOMETRY"] = self.options.core_geometry
        self._cmake.definitions["VXL_BUILD_CORE_SERIALISATION"] = self.options.core_serialisation
        self._cmake.definitions["VXL_BUILD_CORE_UTILITIES"] = self.options.core_utilities
        self._cmake.definitions["VXL_BUILD_CORE_IMAGING"] = self.options.core_imaging
        self._cmake.definitions["VXL_BUILD_EXAMPLES"] = False
        self._cmake.definitions["VXL_BUILD_NONDEPRECATED_ONLY"] = True
        self._cmake.definitions["VXL_BUILD_CORE_PROBABILITY"] = self.options.core_probability
        self._cmake.definitions["VXL_USE_GEOTIFF"] = True
        self._cmake.definitions["VXL_BUILD_CONTRIB"] = False
        self._cmake.definitions["VXL_BUILD_OBJECT_LIBRARIES"] = False

        # core/CMakeLists.txt
        self._cmake.definitions["VXL_BUILD_VGUI"] = False
        self._cmake.definitions["VXL_BUILD_CORE_VIDEO"] = self.options.core_video

        self._cmake.configure()
        return self._cmake

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
