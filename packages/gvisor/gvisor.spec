%global goproject github.com/google
%global gorepo gvisor
%global goimport gvisor.dev/gvisor

%global gitrev 30a83191d380204266349f4f58521134f0f73e52
%global gover 20260928.0

%global _dwz_low_mem_die_limit 0

Name: %{_cross_os}%{gorepo}
Version: %{gover}
Release: 1%{?dist}
Summary: Application kernel for containers (runsc)
License: Apache-2.0 AND MIT AND BSD-3-Clause
URL: https://gvisor.dev
Source0: https://%{goproject}/%{gorepo}/archive/%{gitrev}/%{gorepo}-%{gitrev}.tar.gz
Source1: bundled-%{gorepo}-%{gitrev}.tar.gz
Source2: containerd-gvisor-toml
Source3: runsc-toml
# runsc boots the sandbox from the gvisor_sentry sidecar. Its main package is
# not on the go branch; this is runsc/cmd/sentry/sentry_main.go from the
# release commit (6485c3fbdfe28172ced5d6aed49554cf494967db).
Source4: sentry_main.go

# Confine the sandbox and gofer with the SELinux label CRI assigns to the pod.
Patch0001: 0001-runsc-run-sandbox-and-gofer-under-the-SELinux-process-label.patch

BuildRequires: git

%description
%{summary}.

%prep
%setup -n %{gorepo}-%{gitrev} -q
%setup -T -D -n %{gorepo}-%{gitrev} -b 1
%autopatch -p1

%build
%set_cross_go_flags
export GOTOOLCHAIN=local
# Upstream only supports static, non-cgo builds of runsc and the shim.
export CGO_ENABLED=0
export GOFLAGS="${GOFLAGS//-buildmode=pie/}"

cp %{S:4} runsc/cmd/sentry/
go build -ldflags="-X gvisor.dev/gvisor/runsc/version.version=%{gover}" -o bin/runsc ./runsc
go build -ldflags="-X gvisor.dev/gvisor/runsc/version.version=%{gover}" -o bin/gvisor_sentry ./runsc/cmd/sentry
go build -o bin/containerd-shim-runsc-v1 ./shim

%install
install -d %{buildroot}%{_cross_bindir}
# Bottlerocket's SELinux policy labels /usr/bin/containerd* as runtime_exec_t,
# which runsc needs to run in the container runtime domain. The shim finds the
# binary through `binary_name` in runsc.toml.
install -p -m 0755 bin/runsc %{buildroot}%{_cross_bindir}/containerd-runsc
install -p -m 0755 bin/containerd-shim-runsc-v1 %{buildroot}%{_cross_bindir}
# Sidecars are looked up in gvisor-bin/ next to the runsc binary.
install -d %{buildroot}%{_cross_bindir}/gvisor-bin
install -p -m 0755 bin/gvisor_sentry %{buildroot}%{_cross_bindir}/gvisor-bin

install -d %{buildroot}%{_cross_templatedir}
install -p -m 0644 %{S:2} %{S:3} %{buildroot}%{_cross_templatedir}

%cross_scan_attribution go-vendor vendor

%files
%license LICENSE
%{_cross_attribution_file}
%{_cross_attribution_vendor_dir}
%{_cross_bindir}/containerd-runsc
%{_cross_bindir}/containerd-shim-runsc-v1
%dir %{_cross_bindir}/gvisor-bin
%{_cross_bindir}/gvisor-bin/gvisor_sentry
%{_cross_templatedir}/containerd-gvisor-toml
%{_cross_templatedir}/runsc-toml

%changelog
