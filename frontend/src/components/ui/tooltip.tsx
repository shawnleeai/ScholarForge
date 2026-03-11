import * as React from "react"
import { Tooltip as AntTooltip, TooltipProps as AntTooltipProps } from "antd"
import { cn } from "@/lib/utils"

export interface TooltipProps extends AntTooltipProps {
  className?: string
}

const TooltipProvider = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>
}

const Tooltip = ({ className, children, ...props }: TooltipProps) => {
  return (
    <AntTooltip
      overlayClassName={cn("", className)}
      {...props}
    >
      {children}
    </AntTooltip>
  )
}

const TooltipTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }
>(({ asChild, children, ...props }, ref) => {
  return (
    <button ref={ref} {...props}>
      {children}
    </button>
  )
})
TooltipTrigger.displayName = "TooltipTrigger"

const TooltipContent = ({ children, className, align }: { children?: React.ReactNode; className?: string; align?: string }) => {
  return (
    <div className={cn("", className)}>
      {children}
    </div>
  )
}

export { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent }
