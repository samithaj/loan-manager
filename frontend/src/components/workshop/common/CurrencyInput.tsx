"use client";
import { useState, useEffect } from "react";

interface CurrencyInputProps {
  value: number;
  onChange: (value: number) => void;
  label?: string;
  currency?: string;
  placeholder?: string;
  disabled?: boolean;
  min?: number;
  max?: number;
  className?: string;
  required?: boolean;
}

export default function CurrencyInput({
  value,
  onChange,
  label,
  currency = "USD",
  placeholder = "0.00",
  disabled = false,
  min = 0,
  max,
  className = "",
  required = false,
}: CurrencyInputProps) {
  const [displayValue, setDisplayValue] = useState<string>("");

  useEffect(() => {
    setDisplayValue(value > 0 ? value.toFixed(2) : "");
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    setDisplayValue(inputValue);

    // Parse the input value
    const numericValue = parseFloat(inputValue);
    if (!isNaN(numericValue)) {
      const clampedValue = max ? Math.min(numericValue, max) : numericValue;
      onChange(Math.max(min, clampedValue));
    } else if (inputValue === "") {
      onChange(0);
    }
  };

  const handleBlur = () => {
    // Format on blur
    if (value > 0) {
      setDisplayValue(value.toFixed(2));
    }
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
          {currency === "USD" ? "$" : currency}
        </span>
        <input
          type="text"
          inputMode="decimal"
          value={displayValue}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`
            w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed
            text-right
          `}
        />
      </div>
    </div>
  );
}
