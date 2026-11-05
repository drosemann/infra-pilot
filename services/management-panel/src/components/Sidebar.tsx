import { useNavigate, useLocation } from "react-router";
import { useConfig } from "../lib/types";
import { LanguageSelector } from "../i18n/LanguageSelector";

interface SidebarItem {
  id: string;
  label: string;
  route: string;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
}

const SimpleLogo = ({ size = 32 }: { size?: number }) => (
  <div
    className="flex items-center justify-center rounded-xl bg-white font-bold text-black"
    style={{ width: size, height: size, fontSize: size * 0.4 }}
  >
    IP
  </div>
);

export const Sidebar = ({
  isMobileOpen,
  onMobileClose,
}: {
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mode } = useConfig();

  const sections: SidebarSection[] = [
    {
      title: "Manage",
      items: [
        { id: "overview", label: "Overview", route: "/dashboard" },
        { id: "apps", label: "Apps", route: "/apps" },
        { id: "releases", label: "Releases", route: "/deployments" },
        ...(mode === "business"
          ? [{ id: "customers", label: "Customers", route: "/customers" }]
          : []),
      ],
    },
    {
      title: "Review",
      items: [{ id: "activity", label: "Activity", route: "/activity" }],
    },
    {
      title: "System",
      items: [{ id: "settings", label: "Settings", route: "/settings" }],
    },
  ];

  const isActive = (route: string) => location.pathname.startsWith(route);

  const handleNavigation = (route: string) => {
    navigate(route);
    onMobileClose?.();
  };

  return (
    <>
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={onMobileClose}
        />
      )}
      <div
        className={`fixed md:sticky inset-y-0 left-0 z-30 w-64 h-screen border-r border-white/10 glass-chrome flex flex-col overflow-y-auto transition-transform duration-200 ${isMobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        {/* Logo Section */}
        <div className="p-5 border-b border-white/10">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => {
              navigate("/dashboard");
              onMobileClose?.();
            }}
          >
            <SimpleLogo size={40} />
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-white">
                Infra Pilot
              </h1>
              <p className="text-xs text-white/45">
                {__APP_VERSION__ === "dev" ? "dev" : `v${__APP_VERSION__}`}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-7 p-4" aria-label="Primary navigation">
          {sections.map((section) => (
            <div key={section.title}>
              <p className="px-3 pb-2 text-xs font-medium text-white/40">
                {section.title}
              </p>
              <div className="space-y-1">
                {section.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.route)}
                    aria-current={isActive(item.route) ? "page" : undefined}
                    className={`w-full flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm transition-colors ${
                      isActive(item.route)
                        ? "bg-white font-semibold text-black"
                        : "text-white/65 hover:bg-white/[0.08] hover:text-white"
                    }`}
                  >
                    <span className="flex-1 text-left">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Language */}
        <div className="border-t border-white/10 p-4">
          <div className="px-2">
            <LanguageSelector />
          </div>
        </div>
      </div>
    </>
  );
};
