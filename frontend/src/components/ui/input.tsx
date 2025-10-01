import * as React from "react";
import { cn } from "../../lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex w-full rounded-lg border border-border bg-[rgba(26,32,44,0.6)] px-3.5 py-2.5 text-sm text-foreground backdrop-blur-2xl transition-all duration-200",
          "placeholder:text-muted placeholder:opacity-60",
          "focus:outline-none focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-light)]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex w-full rounded-lg border border-border bg-[rgba(26,32,44,0.6)] px-3.5 py-2.5 text-sm text-foreground backdrop-blur-2xl transition-all duration-200",
          "placeholder:text-muted placeholder:opacity-60",
          "focus:outline-none focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-light)]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "resize-none",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Input, Textarea };
