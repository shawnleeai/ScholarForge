import * as React from "react"
import { Tag as AntTag, TagProps as AntTagProps } from "antd"
import { cn } from "@/lib/utils"

export interface TagProps extends Omit<AntTagProps, 'color'> {
  variant?: "default" | "destructive" | "outline" | "secondary"
  color?: string
  size?: "default" | "small" | "large"
  icon?: React.ReactNode
}

const Tag = React.forwardRef<HTMLSpanElement, TagProps>(
  ({ className, variant = "default", color, size = "default", icon, ...props }, ref) => {
    const colorMap: Record<string, string | undefined> = {
      default: undefined,
      destructive: "error",
      outline: undefined,
      secondary: "warning",
    }

    const variantStyles: Record<string, string> = {
      destructive: "bg-red-100 text-red-800 border-red-200",
      outline: "border-gray-300 bg-white",
      secondary: "bg-gray-100 text-gray-700",
    }

    const sizeMap: Record<string, "default" | "small" | "large"> = {
      default: "default",
      small: "small",
      large: "large",
    }

    return (
      <AntTag
        ref={ref}
        color={color || colorMap[variant]}
        className={cn(
          variantStyles[variant],
          className
        )}
        {...props}
      >
        {icon && <span className="mr-1">{icon}</span>}
        {props.children}
      </AntTag>
    )
  }
)
Tag.displayName = "Tag"

export { Tag }
