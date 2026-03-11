import * as React from "react"
import { Tag, TagProps } from "antd"
import { cn } from "@/lib/utils"

export interface BadgeProps extends TagProps {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info"
  size?: "default" | "sm" | "lg"
}

function Badge({ className, variant = "default", size = "default", children, ...props }: BadgeProps) {
  const variantStyles: Record<string, string> = {
    default: "bg-blue-100 text-blue-800 border-blue-200",
    secondary: "bg-gray-100 text-gray-800 border-gray-200",
    destructive: "bg-red-100 text-red-800 border-red-200",
    outline: "bg-white text-gray-800 border-gray-300",
    success: "bg-green-100 text-green-800 border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
    info: "bg-cyan-100 text-cyan-800 border-cyan-200",
  }

  const sizeStyles: Record<string, string> = {
    default: "px-2.5 py-0.5 text-xs",
    sm: "px-2 py-0 text-xs",
    lg: "px-3 py-1 text-sm",
  }

  return (
    <Tag
      className={cn(
        "inline-flex items-center rounded-full border font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  )
}

export { Badge }
