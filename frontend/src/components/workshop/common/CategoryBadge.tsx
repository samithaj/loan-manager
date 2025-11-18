export type PartCategory =
  | "ENGINE"
  | "BRAKE"
  | "TYRE"
  | "ELECTRICAL"
  | "SUSPENSION"
  | "TRANSMISSION"
  | "EXHAUST"
  | "BODY"
  | "ACCESSORIES"
  | "FLUIDS"
  | "CONSUMABLES"
  | "OTHER";

const categoryColors: Record<PartCategory, string> = {
  ENGINE: "bg-red-100 text-red-800 border-red-200",
  BRAKE: "bg-orange-100 text-orange-800 border-orange-200",
  TYRE: "bg-yellow-100 text-yellow-800 border-yellow-200",
  ELECTRICAL: "bg-blue-100 text-blue-800 border-blue-200",
  SUSPENSION: "bg-indigo-100 text-indigo-800 border-indigo-200",
  TRANSMISSION: "bg-purple-100 text-purple-800 border-purple-200",
  EXHAUST: "bg-gray-100 text-gray-800 border-gray-200",
  BODY: "bg-pink-100 text-pink-800 border-pink-200",
  ACCESSORIES: "bg-cyan-100 text-cyan-800 border-cyan-200",
  FLUIDS: "bg-green-100 text-green-800 border-green-200",
  CONSUMABLES: "bg-lime-100 text-lime-800 border-lime-200",
  OTHER: "bg-gray-100 text-gray-800 border-gray-200",
};

interface CategoryBadgeProps {
  category: PartCategory;
  size?: "sm" | "md" | "lg";
}

export default function CategoryBadge({ category, size = "md" }: CategoryBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
    lg: "px-4 py-1.5 text-base",
  };

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border ${categoryColors[category]} ${sizeClasses[size]}`}
    >
      {category.replace(/_/g, " ")}
    </span>
  );
}
