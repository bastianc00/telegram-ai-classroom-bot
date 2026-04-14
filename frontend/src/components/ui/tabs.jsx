import * as React from "react"

const TabsContext = React.createContext({})

const Tabs = ({ defaultValue, value, onValueChange, children, className = "", ...props }) => {
  const [selectedValue, setSelectedValue] = React.useState(value || defaultValue)

  const handleValueChange = (newValue) => {
    setSelectedValue(newValue)
    if (onValueChange) onValueChange(newValue)
  }

  return (
    <TabsContext.Provider value={{ value: selectedValue, onValueChange: handleValueChange }}>
      <div className={className} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

const TabsList = ({ children, className = "", ...props }) => {
  return (
    <div
      className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

const TabsTrigger = ({ value, children, className = "", ...props }) => {
  const { value: selectedValue, onValueChange } = React.useContext(TabsContext)
  const isSelected = value === selectedValue

  return (
    <button
      type="button"
      onClick={() => onValueChange(value)}
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 ${
        isSelected
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-600 hover:text-gray-900'
      } ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

const TabsContent = ({ value, children, className = "", ...props }) => {
  const { value: selectedValue } = React.useContext(TabsContext)

  if (value !== selectedValue) return null

  return (
    <div className={`mt-2 ${className}`} {...props}>
      {children}
    </div>
  )
}

export { Tabs, TabsContent, TabsList, TabsTrigger }
