"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, PackageReturn, AlertCircle, CheckCircle2 } from "lucide-react";

interface JobPart {
  id: string;
  part_id: string;
  part_code: string;
  part_name: string;
  quantity_used: number;
  unit_cost: number;
  total_cost: number;
  batch_id: string;
}

interface PartReturnFormProps {
  jobId: string;
  jobPart: JobPart;
  onReturnSuccess?: () => void;
}

export function PartReturnForm({ jobId, jobPart, onReturnSuccess }: PartReturnFormProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [returnQuantity, setReturnQuantity] = useState<string>("");
  const [returnReason, setReturnReason] = useState("");
  const [notes, setNotes] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // Validation
    const qty = parseFloat(returnQuantity);
    if (isNaN(qty) || qty <= 0) {
      setError("Please enter a valid quantity");
      return;
    }

    if (qty > jobPart.quantity_used) {
      setError(`Cannot return ${qty} - only ${jobPart.quantity_used} was used`);
      return;
    }

    if (returnReason.length < 5) {
      setError("Please provide a reason (minimum 5 characters)");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`/v1/jobs/${jobId}/parts/return`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          job_part_id: jobPart.id,
          return_quantity: qty,
          return_reason: returnReason,
          notes: notes || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to return part");
      }

      setSuccess(true);
      setReturnQuantity("");
      setReturnReason("");
      setNotes("");

      // Close dialog after short delay
      setTimeout(() => {
        setOpen(false);
        setSuccess(false);
        if (onReturnSuccess) {
          onReturnSuccess();
        }
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <PackageReturn className="mr-2 h-4 w-4" />
          Return Part
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Return Part to Inventory</DialogTitle>
          <DialogDescription>
            Return unused parts from this repair job back to stock
          </DialogDescription>
        </DialogHeader>

        {success && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Part returned successfully!
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Part Info */}
          <div className="rounded-lg border p-3 bg-muted/50">
            <div className="text-sm space-y-1">
              <div className="font-medium">{jobPart.part_name}</div>
              <div className="text-muted-foreground">Code: {jobPart.part_code}</div>
              <div className="text-muted-foreground">
                Quantity Used: <span className="font-medium">{jobPart.quantity_used}</span>
              </div>
              <div className="text-muted-foreground">
                Unit Cost: <span className="font-medium">LKR {jobPart.unit_cost.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Return Quantity */}
          <div className="space-y-2">
            <Label htmlFor="return-quantity">
              Return Quantity <span className="text-red-500">*</span>
            </Label>
            <Input
              id="return-quantity"
              type="number"
              step="0.01"
              min="0"
              max={jobPart.quantity_used}
              value={returnQuantity}
              onChange={(e) => setReturnQuantity(e.target.value)}
              placeholder="Enter quantity to return"
              disabled={loading || success}
              required
            />
            <p className="text-sm text-muted-foreground">
              Maximum: {jobPart.quantity_used}
            </p>
          </div>

          {/* Return Reason */}
          <div className="space-y-2">
            <Label htmlFor="return-reason">
              Return Reason <span className="text-red-500">*</span>
            </Label>
            <Input
              id="return-reason"
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              placeholder="e.g., Part not needed, Wrong part used"
              disabled={loading || success}
              required
              minLength={5}
              maxLength={500}
            />
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Additional Notes</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any additional details..."
              disabled={loading || success}
              rows={3}
              maxLength={1000}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading || success}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {success ? "Returned" : "Return Part"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
