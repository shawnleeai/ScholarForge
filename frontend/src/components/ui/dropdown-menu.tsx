import * as React from "react"
import { Dropdown, Menu, DropdownProps } from "antd"
import { cn } from "@/lib/utils"

export interface DropdownMenuProps extends DropdownProps {
  className?: string
}

const DropdownMenu = ({ className, children, ...props }: DropdownMenuProps) => {
  return (
    <Dropdown overlayClassName={cn("", className)} {...props}>
      {children}
    </Dropdown>
  )
}

const DropdownMenuTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ children, ...props }, ref) => (
    <button ref={ref} {...props}>{children}</button>
  )
)
DropdownMenuTrigger.displayName = "DropdownMenuTrigger"

const DropdownMenuContent = ({ children, className, align }: { children?: React.ReactNode; className?: string; align?: string }) => (
  <div className={cn("min-w-[8rem] overflow-hidden rounded-md border bg-white p-1 shadow-md", className)}>{children}</div>
)

const DropdownMenuItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-gray-100",
        className
      )}
      {...props}
    />
  )
)
DropdownMenuItem.displayName = "DropdownMenuItem"

const DropdownMenuSeparator = ({ className }: { className?: string }) => (
  <div className={cn("-mx-1 my-1 h-px bg-gray-200", className)} />
)

const DropdownMenuLabel = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <div className={cn("px-2 py-1.5 text-sm font-semibold text-gray-500", className)}>{children}</div>
)

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
}
