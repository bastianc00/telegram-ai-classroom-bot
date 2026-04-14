import * as React from "react"

const Select = ({ children, value, onValueChange, disabled = false }) => {
  const [open, setOpen] = React.useState(false)

  // Find the label for the selected value
  const getSelectedLabel = () => {
    let selectedLabel = null
    React.Children.forEach(children, child => {
      if (child.type === SelectContent) {
        React.Children.forEach(child.props.children, item => {
          if (item.type === SelectItem && item.props.value === value) {
            selectedLabel = item.props.children
          }
        })
      }
    })
    return selectedLabel
  }

  return (
    <div className="relative">
      {React.Children.map(children, child => {
        if (child.type === SelectTrigger) {
          return React.cloneElement(child, {
            onClick: () => !disabled && setOpen(!open),
            disabled,
            value,
            selectedLabel: getSelectedLabel()
          })
        }
        if (child.type === SelectContent && open) {
          return React.cloneElement(child, {
            onSelect: (val) => {
              onValueChange(val)
              setOpen(false)
            },
            value
          })
        }
        return null
      })}
    </div>
  )
}

const SelectTrigger = ({ children, onClick, disabled, className = "", selectedLabel, ...props }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    >
      {React.Children.map(children, child => {
        if (child.type === SelectValue) {
          return React.cloneElement(child, { selectedLabel })
        }
        return child
      })}
      <svg className="h-4 w-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
}

const SelectContent = ({ children, onSelect, value }) => {
  return (
    <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-300 bg-white shadow-lg">
      {React.Children.map(children, child => {
        if (child.type === SelectItem) {
          return React.cloneElement(child, {
            onSelect,
            isSelected: child.props.value === value
          })
        }
        return child
      })}
    </div>
  )
}

const SelectItem = ({ children, value, onSelect, isSelected }) => {
  return (
    <div
      onClick={() => onSelect(value)}
      className={`relative flex cursor-pointer select-none items-center py-2 px-3 text-sm hover:bg-gray-100 ${
        isSelected ? 'bg-blue-50 text-blue-600' : ''
      }`}
    >
      {children}
    </div>
  )
}

const SelectValue = ({ placeholder, selectedLabel, ...props }) => {
  const displayValue = selectedLabel || placeholder
  return <span className={!selectedLabel ? 'text-gray-400' : ''}>{displayValue}</span>
}

export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue }
