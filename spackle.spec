# RPM spec for Spackle - SSH/Telnet client for Linux
# Build: ./build_rpm.sh   (creates tarball and runs rpmbuild)

Name:           spackle
Version:        2.0
Release:        1%{?dist}
Summary:        Lightweight SSH/Telnet client with GUI for Linux

License:        MIT
URL:            https://github.com/vuul/spackle-ssh
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       python3
Requires:       python3-tkinter
Requires:       openssh-clients
Requires:       xterm

%description
Spackle is a lightweight SSH/Telnet client for macOS and Linux with a GUI
for managing and launching terminal sessions. This package provides the
Linux build (xterm-based); native Terminal.app is used on macOS.
Features include saved session profiles, terminal customization, and SSH key support.

%prep
%autosetup -n %{name}-%{version}

%install
install -Dm755 spackle.py %{buildroot}%{_bindir}/spackle
install -Dm644 spackle.desktop %{buildroot}%{_datadir}/applications/spackle.desktop

# Optional icon (build works even if icon is missing)
echo "%{_bindir}/spackle" > spackle.files
echo "%{_datadir}/applications/spackle.desktop" >> spackle.files
if [ -f src/spackle/resources/Spackle-icon.png ]; then
  install -Dm644 src/spackle/resources/Spackle-icon.png %{buildroot}%{_datadir}/pixmaps/spackle.png
  echo "%{_datadir}/pixmaps/spackle.png" >> spackle.files
fi

%files -f spackle.files

%changelog
* %(date "+%a %b %d %Y") %{?packager} - %{version}-%{release}
- Initial RPM package for Spackle 2.0
