"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Filter,
  DropletOff,
  FlaskConical,
  Sliders,
  MessagesSquare,
  Map,
  Sparkles,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Executive Dashboard", icon: LayoutDashboard },
  { href: "/funnel", label: "Funnel Analyzer", icon: Filter },
  { href: "/revenue-leaks", label: "Revenue Leak Detector", icon: DropletOff },
  { href: "/experiments", label: "AI Experiment Generator", icon: FlaskConical },
  { href: "/simulator", label: "Revenue Simulator", icon: Sliders },
  { href: "/advisor", label: "AI Founder Advisor", icon: MessagesSquare },
  { href: "/roadmap", label: "AI Roadmap Generator", icon: Map },
  { href: "/growth-twin", label: "Growth Twin Engine", icon: Sparkles },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function NavSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-sidebar md:flex md:flex-col">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Sparkles className="size-5 text-primary" />
        <span className="font-semibold">AI Growth Twin</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname?.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
