import { useEffect, useState, useRef } from "react";
import loanApi from "../api/loanApi";
import "../styles/loans.css";
import PageHeader from "../components/PageHeader";

const today = new Date().toISOString().split("T")[0];

export default function LoansPage() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);

  const [personName, setPersonName] = useState("");
  const [personPhoneNumber, setPersonPhoneNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [type, setType] = useState("lent");
  const [dateCreated, setDateCreated] = useState(today);
  const [dateReturn, setDateReturn] = useState("");

  const [editingLoanId, setEditingLoanId] = useState(null);
  const [editPersonName, setEditPersonName] = useState("");
  const [editPersonPhoneNumber, setEditPersonPhoneNumber] = useState("");
  const [editAmount, setEditAmount] = useState("");
  const [editType, setEditType] = useState("lent");
  const [editStatus, setEditStatus] = useState("unpaid");
  const [editDateReturn, setEditDateReturn] = useState("");
  const [editPaidAmount, setEditPaidAmount] = useState("");
  const [editLastPaymentDate, setEditLastPaymentDate] = useState("");
  const formRef = useRef(null);

  const loadLoans = async () => {
    try {
      setLoading(true);
      const data = await loanApi.getAll();
      setLoans(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to load loans");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLoans();
  }, []);

  useEffect(() => {
    if (editingLoanId && formRef.current) {
      formRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [editingLoanId]);

  const resetCreateForm = () => {
    setPersonName("");
    setPersonPhoneNumber("");
    setAmount("");
    setType("lent");
    setDateCreated(today);
    setDateReturn("");
  };

  const handleCreateLoan = async () => {
    if (!personName || !amount || !type || !dateCreated) {
      alert("Please fill all required fields");
      return;
    }

    try {
      const payload = {
        person_name: personName,
        person_phone_number: personPhoneNumber || null,
        amount: Number(amount),
        type,
        date_created: dateCreated,
      };

      if (dateReturn) {
        payload.date_return = dateReturn;
      }

      await loanApi.create(payload);
      resetCreateForm();
      await loadLoans();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to create loan");
    }
  };

  const startEditLoan = (loan) => {
    setEditingLoanId(loan.id);
    setEditPersonName(loan.person_name || "");
    setEditPersonPhoneNumber(loan.person_phone_number || "");
    setEditAmount(loan.amount ?? "");
    setEditType(loan.type || "lent");
    setEditStatus(loan.status || "unpaid");
    setEditDateReturn(loan.date_return || "");
    setEditPaidAmount(loan.paid_amount ?? "");
    setEditLastPaymentDate(loan.last_payment_date || "");
  };

  const cancelEditLoan = () => {
    setEditingLoanId(null);
    setEditPersonName("");
    setEditPersonPhoneNumber("");
    setEditAmount("");
    setEditType("lent");
    setEditStatus("unpaid");
    setEditDateReturn("");
    setEditPaidAmount("");
    setEditLastPaymentDate("");
  };

  const handleUpdateLoan = async () => {
    if (!editingLoanId) return;

    const payload = {
      person_name: editPersonName,
      person_phone_number: editPersonPhoneNumber || null,
      amount: Number(editAmount),
      type: editType,
      status: editStatus,
    };

    if (editStatus === "paid") {
      if (!editDateReturn) {
        alert("Return date is required when status is paid");
        return;
      }

      payload.date_return = editDateReturn;
    }

    if (editStatus === "partially_paid") {
      if (!editPaidAmount || !editLastPaymentDate) {
        alert("Paid amount and payment date are required for partially paid loans");
        return;
      }

      payload.paid_amount = Number(editPaidAmount);
      payload.last_payment_date = editLastPaymentDate;
    }

    try {
      await loanApi.update(editingLoanId, payload);
      cancelEditLoan();
      await loadLoans();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to update loan");
    }
  };

  const handleDeleteLoan = async (id) => {
    if (!window.confirm("Are you sure you want to delete this loan?")) return;

    try {
      await loanApi.remove(id);
      await loadLoans();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to delete loan");
    }
  };

  return (
    <div className="loans-page">
      <PageHeader title="Loans" />

      <div className="loans-layout">
        <div className="loan-side-panel">
          {!editingLoanId ? (
            <div ref={formRef} className="loan-form form-panel">
              <h3 className="section-title">Create Loan</h3>

              <label>Person Name</label>
              <input value={personName} onChange={(e) => setPersonName(e.target.value)} />

              <label>Phone Number</label>
              <input
                value={personPhoneNumber}
                onChange={(e) => setPersonPhoneNumber(e.target.value)}
              />

              <label>Amount</label>
              <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />

              <label>Loan Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                <option value="lent">Lent</option>
                <option value="borrowed">Borrowed</option>
              </select>

              <label>Date Created</label>
              <input
                type="date"
                value={dateCreated}
                onChange={(e) => setDateCreated(e.target.value)}
              />

              <label>Expected Return Date (optional)</label>
              <input type="date" value={dateReturn} onChange={(e) => setDateReturn(e.target.value)} />

              <button className="btn btn-primary btn-full" onClick={handleCreateLoan}>
                Create Loan
              </button>
            </div>
          ) : (
            <div ref={formRef} className="loan-form form-panel">
              <h3 className="section-title">Edit Loan</h3>

              <label>Person Name</label>
              <input value={editPersonName} onChange={(e) => setEditPersonName(e.target.value)} />

              <label>Phone Number</label>
              <input
                value={editPersonPhoneNumber}
                onChange={(e) => setEditPersonPhoneNumber(e.target.value)}
              />

              <label>Amount</label>
              <input type="number" value={editAmount} onChange={(e) => setEditAmount(e.target.value)} />

              <label>Loan Type</label>
              <select value={editType} onChange={(e) => setEditType(e.target.value)}>
                <option value="lent">Lent</option>
                <option value="borrowed">Borrowed</option>
              </select>

              <label>Status</label>
              <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                <option value="unpaid">Unpaid</option>
                <option value="partially_paid">Partially Paid</option>
                <option value="paid">Paid</option>
                <option value="overdue">Overdue</option>
              </select>

              {editStatus === "paid" && (
                <>
                  <label>Return Date</label>
                  <input
                    type="date"
                    value={editDateReturn}
                    onChange={(e) => setEditDateReturn(e.target.value)}
                  />
                </>
              )}

              {editStatus === "partially_paid" && (
                <>
                  <label>Paid Amount</label>
                  <input
                    type="number"
                    value={editPaidAmount}
                    onChange={(e) => setEditPaidAmount(e.target.value)}
                  />

                  <label>Last Payment Date</label>
                  <input
                    type="date"
                    value={editLastPaymentDate}
                    onChange={(e) => setEditLastPaymentDate(e.target.value)}
                  />
                </>
              )}

              <div className="edit-actions">
                <button className="btn btn-primary btn-half" onClick={handleUpdateLoan}>
                  Save Changes
                </button>

                <button className="btn btn-edit btn-half" onClick={cancelEditLoan}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="loan-list-panel list-panel">
          <h3 className="section-title">Loan List</h3>

          {loading ? (
            <p>Loading...</p>
          ) : loans.length === 0 ? (
            <p>No loans found.</p>
          ) : (
            <div className="loan-table-wrapper table-scroll">
              <table className="loan-table sticky-table">
                <thead>
                  <tr>
                    <th>Person</th>
                    <th>Phone</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Type</th>
                    <th>Date Created</th>
                    <th>Date Return</th>
                    <th>Paid Amount</th>
                    <th>Last Payment Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {loans.map((loan) => (
                    <tr key={loan.id}>
                      <td>{loan.person_name}</td>
                      <td>{loan.person_phone_number}</td>
                      <td>{loan.amount}</td>
                      <td>{loan.status}</td>
                      <td>{loan.type}</td>
                      <td>{loan.date_created}</td>
                      <td>{loan.date_return || "-"}</td>
                      <td>{loan.paid_amount ?? 0}</td>
                      <td>{loan.last_payment_date || "-"}</td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn btn-edit btn-action"
                            onClick={() => startEditLoan(loan)}
                          >
                            <span className="btn-icon">✏️</span>
                            <span className="btn-label">Edit</span>
                          </button>

                          <button
                            className="btn btn-delete btn-action"
                            onClick={() => handleDeleteLoan(loan.id)}
                          >
                            <span className="btn-icon">🗑️</span>
                            <span className="btn-label">Delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}