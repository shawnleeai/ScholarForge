import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { Button as AntButton, ButtonProps as AntButtonProps } from "antd"
import { cn } from "@/lib/utils"

export interface ButtonProps extends Omit<AntButtonProps, 'type' | 'size'> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "primary" | "dashed" | "text"
  size?: "default" | "sm" | "lg" | "icon" | "small" | "middle" | "large"
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    // 映射 variant 到 Ant Design 的 type
    const typeMap: Record<string, AntButtonProps['type']> = {
      default: "primary",
      destructive: "primary",
      outline: "default",
      secondary: "default",
      ghost: "text",
      link: "link",
      primary: "primary",
      dashed: "dashed",
      text: "text",
    }

    // 映射 size
    const sizeMap: Record<string, AntButtonProps['size']> = {
      default: "middle",
      sm: "small",
      lg: "large",
      icon: "middle",
      small: "small",
      middle: "middle",
      large: "large",
    }

    const variantStyles: Record<string, string> = {
      destructive: "bg-red-600 hover:bg-red-700 border-red-600",
      outline: "border-gray-300 bg-white hover:bg-gray-50",
      secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
      ghost: "hover:bg-gray-100",
      link: "text-blue-600 hover:underline p-0 h-auto",
    }

    const Comp = asChild ? Slot : "button"

    if (asChild) {
      return (
        <Slot
          className={cn(
            variantStyles[variant],
            className
          )}
          {...props}
        >
          {props.children}
        </Slot>
      )
    }

    return (
      <AntButton
        ref={ref}
        type={typeMap[variant]}
        size={sizeMap[size]}
        className={cn(
          variantStyles[variant],
          className
        )}
        danger={variant === "destructive"}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
