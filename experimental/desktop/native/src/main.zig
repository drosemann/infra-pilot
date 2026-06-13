const std = @import("std");
const build_options = @import("build_options");
const zero_native = @import("zero-native");

pub const panic = std.debug.FullPanic(zero_native.debug.capturePanic);

const frontend_dist = "dist";
const dev_origins = [_][]const u8{
    "zero://app",
    "zero://inline",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3001",
};

const PanelApp = struct {
    env_map: *std.process.Environ.Map,

    fn app(self: *@This()) zero_native.App {
        return .{
            .context = self,
            .name = "infra-pilot-panel",
            .source = zero_native.frontend.productionSource(.{
                .dist = frontend_dist,
                .entry = "index.html",
            }),
            .source_fn = source,
        };
    }

    fn source(context: *anyopaque) anyerror!zero_native.WebViewSource {
        const self: *PanelApp = @ptrCast(@alignCast(context));
        return zero_native.frontend.sourceFromEnv(self.env_map, .{
            .dist = frontend_dist,
            .entry = "index.html",
            .spa_fallback = true,
        });
    }
};

pub fn main(init: std.process.Init) !void {
    var panel = PanelApp{ .env_map = init.environ_map };
    var app_info = zero_native.AppInfo{
        .app_name = "Infra Pilot Panel",
        .window_title = "Infra Pilot Panel",
        .bundle_id = "dev.infra_pilot.management_panel",
        .icon_path = "native/assets/icon.svg",
    };

    var platform = try createPlatform(app_info);
    defer platform.deinit();

    var trace_sink = StdoutTraceSink{};
    var runtime = zero_native.Runtime.init(.{
        .platform = platform.platform(),
        .trace_sink = trace_sink.sink(),
        .security = .{
            .navigation = .{
                .allowed_origins = &dev_origins,
                .external_links = .{ .action = .deny },
            },
        },
    });

    try runtime.run(panel.app());
}

const PlatformHost = union(enum) {
    null: zero_native.NullPlatform,
    macos: zero_native.platform.macos.MacPlatform,
    linux: zero_native.platform.linux.LinuxPlatform,
    windows: zero_native.platform.windows.WindowsPlatform,

    fn platform(self: *@This()) zero_native.Platform {
        return switch (self.*) {
            .null => |*host| host.platform(),
            .macos => |*host| host.platform(),
            .linux => |*host| host.platform(),
            .windows => |*host| host.platform(),
        };
    }

    fn deinit(self: *@This()) void {
        switch (self.*) {
            .null => {},
            .macos => |*host| host.deinit(),
            .linux => |*host| host.deinit(),
            .windows => |*host| host.deinit(),
        }
    }
};

fn createPlatform(app_info: zero_native.AppInfo) !PlatformHost {
    const size = zero_native.geometry.SizeF.init(1280, 820);
    const engine: zero_native.WebEngine = if (comptime std.mem.eql(u8, build_options.web_engine, "chromium")) .chromium else .system;

    if (comptime std.mem.eql(u8, build_options.platform, "macos")) {
        return .{ .macos = try zero_native.platform.macos.MacPlatform.initWithOptions(size, engine, app_info) };
    }
    if (comptime std.mem.eql(u8, build_options.platform, "linux")) {
        return .{ .linux = try zero_native.platform.linux.LinuxPlatform.initWithOptions(size, engine, app_info) };
    }
    if (comptime std.mem.eql(u8, build_options.platform, "windows")) {
        return .{ .windows = try zero_native.platform.windows.WindowsPlatform.initWithOptions(size, engine, app_info) };
    }
    return .{ .null = zero_native.NullPlatform.initWithOptions(.{}, engine, app_info) };
}

pub const StdoutTraceSink = struct {
    pub fn sink(self: *StdoutTraceSink) zero_native.trace.Sink {
        return .{ .context = self, .write_fn = write };
    }

    fn write(context: *anyopaque, record: zero_native.trace.Record) zero_native.trace.WriteError!void {
        _ = context;
        if (comptime std.mem.eql(u8, build_options.trace, "off")) return;
        var buffer: [1024]u8 = undefined;
        var writer = std.Io.Writer.fixed(&buffer);
        zero_native.trace.formatText(record, &writer) catch return error.OutOfSpace;
        std.debug.print("{s}\n", .{writer.buffered()});
    }
};

test "production source points at the Vite dist directory" {
    const source = zero_native.frontend.productionSource(.{
        .dist = frontend_dist,
        .entry = "index.html",
    });
    try std.testing.expectEqual(zero_native.WebViewSourceKind.assets, source.kind);
    try std.testing.expectEqualStrings(frontend_dist, source.asset_options.?.root_path);
}
