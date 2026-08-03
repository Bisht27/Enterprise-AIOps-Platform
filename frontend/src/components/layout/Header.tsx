import NotificationBell from "./NotificationBell";

export default function Header() {
  return (
    <header className="bg-white shadow px-6 py-4 flex items-center justify-between">
      <h1 className="text-2xl font-bold">
        AI Infrastructure Operations Platform
      </h1>
      <NotificationBell />
    </header>
  );
}