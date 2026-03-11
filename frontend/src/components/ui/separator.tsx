import * as React from "react"
import { Divider, DividerProps } from "antd"
import { cn } from "@/lib/utils"

export interface SeparatorProps extends DividerProps {
  className?: string
  orientation?: "horizontal" | "vertical"
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = "horizontal", ...props }, ref) => (
    <Divider
      ref={ref}
      type={orientation === "vertical" ? "vertical" : "horizontal"}
      className={cn("bg-gray-200", className)}
      {...props}
    />
  )
)
Separator.displayName = "Separator"

export { Separator }
