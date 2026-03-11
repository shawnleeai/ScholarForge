import * as React from "react"
import { Modal, ModalProps } from "antd"
import { cn } from "@/lib/utils"

export interface DialogProps extends Omit<ModalProps, 'onCancel'> {
  className?: string
  onOpenChange?: (open: boolean) => void
}

const Dialog = ({ className, onOpenChange, ...props }: DialogProps) => {
  return (
    <Modal
      className={cn("", className)}
      onCancel={() => onOpenChange?.(false)}
      {...props}
    />
  )
}

const DialogTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ children, ...props }, ref) => (
    <button ref={ref} {...props}>{children}</button>
  )
)
DialogTrigger.displayName = "DialogTrigger"

const DialogContent = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <div className={cn("", className)}>{children}</div>
)

const DialogHeader = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left mb-4", className)}>{children}</div>
)

const DialogTitle = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <h3 className={cn("text-lg font-semibold leading-none tracking-tight", className)}>{children}</h3>
)

const DialogDescription = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <p className={cn("text-sm text-gray-500", className)}>{children}</p>
)

const DialogFooter = ({ children, className }: { children?: React.ReactNode; className?: string }) => (
  <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-4", className)}>{children}</div>
)

export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
}
