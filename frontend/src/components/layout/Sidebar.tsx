import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Monitor,
  TriangleAlert,
  Ticket,
  FileText,
  Settings,
  QrCode,
  Bell,
} from "lucide-react";

const menus = [
  // Live monitoring now lives on the Dashboard itself (asset dropdown
  // + live panel), so the separate "Monitoring" nav item is removed.
  // The /monitoring route and page still exist and keep working.
  { title: "Dashboard", icon: LayoutDashboard, path: "/" },
  { title: "Assets", icon: Monitor, path: "/assets" },
  { title: "QR Assets", icon: QrCode, path: "/assets/qr" },
  { title: "Alerts", icon: TriangleAlert, path: "/alerts" },
  { title: "Tickets", icon: Ticket, path: "/tickets" },
  { title: "Reports", icon: FileText, path: "/reports" },
  { title: "Notifications", icon: Bell, path: "/notifications" },
  { title: "Settings", icon: Settings, path: "/settings" },
];

const Sidebar = () => {
  return (
    <aside className="w-64 bg-slate-900 text-white h-screen fixed left-0 top-0 overflow-y-auto">
      <div className="p-6 text-2xl font-bold border-b border-slate-700">
        AIOps
      </div>

      <nav className="mt-6">
        {menus.map((menu) => (
          <NavLink
            key={menu.title}
            to={menu.path}
            end={menu.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-4 px-6 py-4 hover:bg-slate-800 cursor-pointer transition ${
                isActive ? "bg-slate-800 border-l-4 border-blue-500" : ""
              }`
            }
          >
            <menu.icon size={20} />
            <span>{menu.title}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
