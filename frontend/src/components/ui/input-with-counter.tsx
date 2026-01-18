"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Input } from "./input"

interface InputWithCounterProps extends React.ComponentProps<"input"> {
  maxLength: number
  showCount?: boolean
}

function InputWithCounter({
  className,
  maxLength,
  showCount = true,
  value,
  defaultValue,
  onChange,
  ...props
}: InputWithCounterProps) {
  const [internalValue, setInternalValue] = React.useState(
    (defaultValue as string) || ""
  )

  const currentValue = value !== undefined ? String(value) : internalValue
  const currentLength = currentValue.length
  const isOverLimit = currentLength > maxLength
  const isNearLimit = currentLength >= maxLength * 0.9

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (value === undefined) {
      setInternalValue(e.target.value)
    }
    onChange?.(e)
  }

  return (
    <div className="relative w-full">
      <Input
        className={cn(
          showCount && "pr-16",
          isOverLimit && "border-destructive focus-visible:border-destructive",
          className
        )}
        value={value}
        defaultValue={defaultValue}
        onChange={handleChange}
        maxLength={undefined}
        {...props}
      />
      {showCount && (
        <div
          className={cn(
            "absolute right-3 top-1/2 -translate-y-1/2 text-xs tabular-nums pointer-events-none",
            isOverLimit
              ? "text-destructive font-medium"
              : isNearLimit
                ? "text-amber-500"
                : "text-muted-foreground"
          )}
        >
          {currentLength}/{maxLength}
        </div>
      )}
    </div>
  )
}

export { InputWithCounter }
