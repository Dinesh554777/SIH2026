import React from "react";
import { Outlet } from "react-router-dom";
import CommandBar from "../components/commandbar/CommandBar.jsx";
import Sidebar from "../components/navigation/Sidebar.jsx";

export default function AppLayout({ breadcrumb }) {
  return (
    <div className="app-shell">
      <CommandBar breadcrumb={breadcrumb} />
      <div className="app-body">
        <Sidebar />
        <div className="app-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
