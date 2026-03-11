import * as React from "react"
import { Input as AntInput, InputProps as AntInputProps } from "antd"
import { cn } from "@/lib/utils"

export interface InputProps extends Omit<AntInputProps, 'size'> {
  size?: "default" | "sm" | "lg"
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, size = "default", ...props }, ref) => {
    const sizeMap: Record<string, AntInputProps['size']> = {
      default: "middle",
      sm: "small",
      lg: "large",
    }

    return (
      <AntInput
        ref={ref}
        size={sizeMap[size]}
        className={cn(
          "flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
