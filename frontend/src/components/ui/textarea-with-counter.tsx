"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Textarea } from "./textarea"

interface TextareaWithCounterProps
  extends React.ComponentProps<"textarea"> {
  maxLength: number
  showCount?: boolean
}

function TextareaWithCounter({
  className,
  maxLength,
  showCount = true,
  value,
  defaultValue,
  onChange,
  ...props
}: TextareaWithCounterProps) {
  const [internalValue, setInternalValue] = React.useState(
    (defaultValue as string) || ""
  )

  const currentValue = value !== undefined ? String(value) : internalValue
  const currentLength = currentValue.length
  const isOverLimit = currentLength > maxLength
  const isNearLimit = currentLength >= maxLength * 0.9

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (value === undefined) {
      setInternalValue(e.target.value)
    }
    onChange?.(e)
  }

  return (
    <div className="relative w-full">
      <Textarea
        className={cn(
          showCount && "pb-7",
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
            "absolute bottom-2 right-3 text-xs tabular-nums",
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

export { TextareaWithCounter }
