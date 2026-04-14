import * as React from "react"

const alertVariants = {
  default: "bg-white border-gray-200",
  destructive: "bg-red-50 border-red-200 text-red-900",
}

function Alert({ className = "", variant = "default", ...props }) {
  const variantClass = alertVariants[variant] || alertVariants.default

  return (
    <div
      role="alert"
      className={`relative w-full rounded-lg border p-4 ${variantClass} ${className}`}
      {...props}
    />
  )
}

function AlertDescription({ className = "", ...props }) {
  return (
    <div
      className={`text-sm [&_p]:leading-relaxed ${className}`}
      {...props}
    />
  )
}

export { Alert, AlertDescription }
