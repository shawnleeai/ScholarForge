import * as React from "react"
import { Progress as AntProgress, ProgressProps } from "antd"
import { cn } from "@/lib/utils"

export interface ProgressComponentProps extends Omit<ProgressProps, 'percent'> {
  className?: string
  value?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressComponentProps>(
  ({ className, value, ...props }, ref) => (
    <div ref={ref} className={cn("relative w-full", className)}>
      <AntProgress percent={value} {...props} />
    </div>
  )
)
Progress.displayName = "Progress"

export { Progress }
