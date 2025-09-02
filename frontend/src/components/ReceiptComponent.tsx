import React, { forwardRef } from "react";

type Transaction = {
  id: string;
  loanId: string;
  type: string;
  amount: number;
  date: string;
  receiptNumber: string;
  postedBy?: string | null;
};

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
  createdOn: string;
};

interface ReceiptProps {
  loan: Loan;
  transaction: Transaction;
  clientName?: string;
}

const ReceiptComponent = forwardRef<HTMLDivElement, ReceiptProps>(
  ({ loan, transaction, clientName }, ref) => {
    const formatCurrency = (amount: number) => `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    return (
      <div ref={ref} className="bg-white p-8 max-w-md mx-auto font-mono text-sm">
        {/* Header */}
        <div className="text-center border-b-2 border-gray-800 pb-4 mb-6">
          <h1 className="text-xl font-bold">LOAN MANAGER</h1>
          <p className="text-gray-600">Transaction Receipt</p>
        </div>

        {/* Receipt Details */}
        <div className="space-y-3 mb-6">
          <div className="flex justify-between">
            <span className="font-bold">Receipt #:</span>
            <span>{transaction.receiptNumber}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-bold">Date:</span>
            <span>{new Date(transaction.date).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-bold">Time:</span>
            <span>{new Date().toLocaleTimeString()}</span>
          </div>
        </div>

        {/* Loan Information */}
        <div className="border-t border-gray-300 pt-4 mb-6">
          <h3 className="font-bold mb-3">LOAN INFORMATION</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Loan ID:</span>
              <span>{loan.id}</span>
            </div>
            <div className="flex justify-between">
              <span>Client:</span>
              <span>{clientName || loan.clientId}</span>
            </div>
            <div className="flex justify-between">
              <span>Principal:</span>
              <span>{formatCurrency(loan.principal)}</span>
            </div>
          </div>
        </div>

        {/* Transaction Information */}
        <div className="border-t border-gray-300 pt-4 mb-6">
          <h3 className="font-bold mb-3">TRANSACTION DETAILS</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Type:</span>
              <span className="uppercase">{transaction.type}</span>
            </div>
            <div className="flex justify-between font-bold text-lg">
              <span>Amount:</span>
              <span>{formatCurrency(transaction.amount)}</span>
            </div>
            {transaction.postedBy && (
              <div className="flex justify-between">
                <span>Posted By:</span>
                <span>{transaction.postedBy}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t-2 border-gray-800 pt-4 text-center text-xs text-gray-600">
          <p>Thank you for your payment</p>
          <p className="mt-2">This is an official receipt</p>
          <p className="mt-4">Generated on {new Date().toLocaleString()}</p>
        </div>
      </div>
    );
  }
);

ReceiptComponent.displayName = "ReceiptComponent";

export default ReceiptComponent;