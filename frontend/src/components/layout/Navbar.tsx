import { useState } from "react";
import { UserCircle, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import NotificationBell from "./NotificationBell";

const Navbar = () => {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="h-16 bg-white shadow flex justify-between items-center px-8 relative">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="flex items-center gap-6">
        <NotificationBell />

        <div className="relative">
          <button
            className="flex items-center gap-2"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <UserCircle size={34} />
            {user && (
              <span className="text-sm font-medium hidden sm:inline">
                {user.full_name}
              </span>
            )}
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-44 bg-white rounded-lg shadow-lg border py-1 z-50">
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-slate-50"
              >
                <LogOut size={16} />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
