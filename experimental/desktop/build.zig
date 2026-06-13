const std = @import("std");

const PlatformOption = enum { auto, null, macos, linux, windows };
const TraceOption = enum { off, events, runtime, all };
const WebEngineOption = enum { system, chromium };
const PackageTarget = enum { macos, linux, windows };

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const platform_option = b.option(PlatformOption, "platform", "Desktop backend: auto, null, macos, linux, windows") orelse .auto;
    const trace_option = b.option(TraceOption, "trace", "Trace output: off, events, runtime, all") orelse .events;
    const web_engine = b.option(WebEngineOption, "web-engine", "Web engine: system, chromium") orelse .system;
    const package_target = b.option(PackageTarget, "package-target", "Package target: macos, linux, windows") orelse .macos;
    const zero_native_path = b.option([]const u8, "zero-native-path", "Path to a zero-native framework checkout") orelse "../../vendor/zero-native";

    const selected_platform = resolvePlatform(target, platform_option);
    const zero_native_mod = zeroNativeModule(b, target, optimize, zero_native_path);

    const options = b.addOptions();
    options.addOption([]const u8, "platform", @tagName(selected_platform));
    options.addOption([]const u8, "trace", @tagName(trace_option));
    options.addOption([]const u8, "web_engine", @tagName(web_engine));

    const app_mod = b.createModule(.{
        .root_source_file = b.path("native/src/main.zig"),
        .target = target,
        .optimize = optimize,
    });
    app_mod.addImport("zero-native", zero_native_mod);
    app_mod.addImport("build_options", options.createModule());

    const exe = b.addExecutable(.{
        .name = "infra-pilot-panel",
        .root_module = app_mod,
    });
    linkPlatform(b, app_mod, exe, selected_platform, web_engine, zero_native_path);
    b.installArtifact(exe);

    const frontend_install = b.addSystemCommand(&.{ "npm", "install" });
    const frontend_install_step = b.step("frontend-install", "Install management-panel dependencies");
    frontend_install_step.dependOn(&frontend_install.step);

    const frontend_build = b.addSystemCommand(&.{ "npm", "run", "build" });
    frontend_build.step.dependOn(&frontend_install.step);
    const frontend_build_step = b.step("frontend-build", "Build the Vite frontend");
    frontend_build_step.dependOn(&frontend_build.step);

    const run = b.addRunArtifact(exe);
    run.step.dependOn(&frontend_build.step);
    const run_step = b.step("run", "Build the frontend and run the native panel shell");
    run_step.dependOn(&run.step);

    const dev = b.addSystemCommand(&.{ "zero-native", "dev", "--manifest", "app.zon", "--binary" });
    dev.addFileArg(exe.getEmittedBin());
    dev.step.dependOn(&exe.step);
    dev.step.dependOn(&frontend_install.step);
    const dev_step = b.step("dev", "Run the Vite dev server and native panel shell");
    dev_step.dependOn(&dev.step);

    const package = b.addSystemCommand(&.{
        "zero-native", "package",
        "--target", @tagName(package_target),
        "--manifest", "app.zon",
        "--assets", "dist",
        "--output", b.fmt("zig-out/package/infra-pilot-panel-0.0.1-{s}", .{@tagName(package_target)}),
        "--binary",
    });
    package.addFileArg(exe.getEmittedBin());
    package.step.dependOn(&exe.step);
    package.step.dependOn(&frontend_build.step);
    const package_step = b.step("package", "Create a distributable zero-native package");
    package_step.dependOn(&package.step);

    const tests = b.addTest(.{ .root_module = app_mod });
    const test_step = b.step("test", "Run native shell tests");
    test_step.dependOn(&b.addRunArtifact(tests).step);
}

fn resolvePlatform(target: std.Build.ResolvedTarget, platform: PlatformOption) PlatformOption {
    return switch (platform) {
        .auto => switch (target.result.os.tag) {
            .macos => .macos,
            .linux => .linux,
            .windows => .windows,
            else => .null,
        },
        else => platform,
    };
}

fn zeroNativeModule(b: *std.Build, target: std.Build.ResolvedTarget, optimize: std.builtin.OptimizeMode, root: []const u8) *std.Build.Module {
    const geometry_mod = externalModule(b, target, optimize, root, "src/primitives/geometry/root.zig");
    const assets_mod = externalModule(b, target, optimize, root, "src/primitives/assets/root.zig");
    const app_dirs_mod = externalModule(b, target, optimize, root, "src/primitives/app_dirs/root.zig");
    const trace_mod = externalModule(b, target, optimize, root, "src/primitives/trace/root.zig");
    const app_manifest_mod = externalModule(b, target, optimize, root, "src/primitives/app_manifest/root.zig");
    const diagnostics_mod = externalModule(b, target, optimize, root, "src/primitives/diagnostics/root.zig");
    const platform_info_mod = externalModule(b, target, optimize, root, "src/primitives/platform_info/root.zig");
    const json_mod = externalModule(b, target, optimize, root, "src/primitives/json/root.zig");
    const debug_mod = externalModule(b, target, optimize, root, "src/debug/root.zig");
    debug_mod.addImport("app_dirs", app_dirs_mod);
    debug_mod.addImport("trace", trace_mod);

    const zero_native_mod = externalModule(b, target, optimize, root, "src/root.zig");
    zero_native_mod.addImport("geometry", geometry_mod);
    zero_native_mod.addImport("assets", assets_mod);
    zero_native_mod.addImport("app_dirs", app_dirs_mod);
    zero_native_mod.addImport("trace", trace_mod);
    zero_native_mod.addImport("app_manifest", app_manifest_mod);
    zero_native_mod.addImport("diagnostics", diagnostics_mod);
    zero_native_mod.addImport("platform_info", platform_info_mod);
    zero_native_mod.addImport("json", json_mod);
    zero_native_mod.addImport("debug", debug_mod);
    return zero_native_mod;
}

fn externalModule(b: *std.Build, target: std.Build.ResolvedTarget, optimize: std.builtin.OptimizeMode, root: []const u8, path: []const u8) *std.Build.Module {
    return b.createModule(.{
        .root_source_file = .{ .cwd_relative = b.pathJoin(&.{ root, path }) },
        .target = target,
        .optimize = optimize,
    });
}

fn zeroNativePath(b: *std.Build, root: []const u8, path: []const u8) std.Build.LazyPath {
    return .{ .cwd_relative = b.pathJoin(&.{ root, path }) };
}

fn linkPlatform(b: *std.Build, app_mod: *std.Build.Module, exe: *std.Build.Step.Compile, platform: PlatformOption, web_engine: WebEngineOption, root: []const u8) void {
    _ = exe;
    if (platform == .macos) {
        app_mod.addCSourceFile(.{ .file = zeroNativePath(b, root, "src/platform/macos/appkit_host.m"), .flags = &.{ "-fobjc-arc", "-ObjC", "-mmacosx-version-min=11.0" } });
        app_mod.linkFramework("WebKit", .{});
        app_mod.linkFramework("AppKit", .{});
        app_mod.linkFramework("Foundation", .{});
        app_mod.linkFramework("UniformTypeIdentifiers", .{});
        app_mod.linkSystemLibrary("c", .{});
    } else if (platform == .linux) {
        app_mod.addCSourceFile(.{ .file = zeroNativePath(b, root, "src/platform/linux/gtk_host.c"), .flags = &.{} });
        app_mod.linkSystemLibrary("gtk4", .{});
        app_mod.linkSystemLibrary("webkitgtk-6.0", .{});
        app_mod.linkSystemLibrary("c", .{});
    } else if (platform == .windows) {
        app_mod.addCSourceFile(.{ .file = zeroNativePath(b, root, "src/platform/windows/webview2_host.cpp"), .flags = &.{"-std=c++17"} });
        app_mod.linkSystemLibrary("c", .{});
        app_mod.linkSystemLibrary("c++", .{});
        app_mod.linkSystemLibrary("user32", .{});
        app_mod.linkSystemLibrary("ole32", .{});
        app_mod.linkSystemLibrary("shell32", .{});
    }

    if (web_engine == .chromium) {
        @panic("Chromium/CEF packaging is documented in app.zon but this local build graph currently supports the system WebView path only.");
    }
}
