import * as React from "react"

const badgeVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
  outline: "border border-gray-300 text-gray-700 hover:bg-gray-100",
  destructive: "bg-red-600 text-white hover:bg-red-700",
}

function Badge({ className = "", variant = "default", ...props }) {
  const variantClass = badgeVariants[variant] || badgeVariants.default

  return (
    <div
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${variantClass} ${className}`}
      {...props}
    />
  )
}

export { Badge }
