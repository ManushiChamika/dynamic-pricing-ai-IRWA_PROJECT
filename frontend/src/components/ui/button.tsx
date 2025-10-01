import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-lg font-medium text-sm transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent",
          "disabled:pointer-events-none disabled:opacity-50 disabled:saturate-[0.4]",
          "relative overflow-hidden backdrop-blur-2xl",
          "before:content-[''] before:absolute before:inset-0 before:transition-opacity before:duration-300 before:opacity-0",
          "hover:not(:disabled):before:opacity-100 active:not(:disabled):translate-y-0",
          {
            default: "bg-gradient-to-br from-[rgba(30,41,59,0.8)] to-[rgba(26,32,44,0.9)] border border-border shadow-[0_2px_6px_rgba(0,0,0,0.4),0_1px_3px_rgba(0,0,0,0.3)] before:bg-gradient-to-br before:from-accent before:to-accent-hover hover:not(:disabled):border-accent hover:not(:disabled):text-white hover:not(:disabled):-translate-y-0.5 hover:not(:disabled):shadow-[0_6px_12px_rgba(99,102,241,0.3),0_2px_4px_rgba(99,102,241,0.2)] active:not(:disabled):shadow-[0_2px_4px_rgba(99,102,241,0.2)]",
            secondary: "bg-gradient-to-br from-[rgba(30,41,59,0.8)] to-[rgba(26,32,44,0.9)] border border-border shadow-[0_2px_6px_rgba(0,0,0,0.4),0_1px_3px_rgba(0,0,0,0.3)] before:bg-gradient-to-br before:from-accent before:to-accent-hover hover:not(:disabled):border-accent hover:not(:disabled):text-white hover:not(:disabled):-translate-y-0.5 hover:not(:disabled):shadow-[0_6px_12px_rgba(99,102,241,0.3),0_2px_4px_rgba(99,102,241,0.2)] active:not(:disabled):shadow-[0_2px_4px_rgba(99,102,241,0.2)]",
            destructive: "bg-gradient-to-br from-red-600 to-red-700 text-white border-0 shadow-[0_2px_6px_rgba(239,68,68,0.4)] before:bg-gradient-to-br before:from-red-500 before:to-red-600 hover:not(:disabled):-translate-y-0.5 hover:not(:disabled):shadow-[0_6px_12px_rgba(239,68,68,0.4)]",
            outline: "border border-border bg-transparent hover:not(:disabled):bg-accent/10 hover:not(:disabled):border-accent",
            ghost: "border-0 shadow-none hover:not(:disabled):bg-accent/10",
          }[variant],
          {
            default: "h-9 px-4 py-2",
            sm: "h-8 px-3 text-xs",
            lg: "h-10 px-8",
            icon: "h-9 w-9 p-0",
          }[size],
          className
        )}
        ref={ref}
        {...props}
      >
        <span className="relative z-10">{props.children}</span>
      </button>
    );
  }
);
Button.displayName = "Button";

export { Button };
