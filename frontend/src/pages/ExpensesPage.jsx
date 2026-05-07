import { useEffect, useState } from "react";
import expenseApi from "../api/expenseApi";
import categoryApi from "../api/categoryApi";
import "../styles/expenses.css";
import PageHeader from "../components/PageHeader";

const today = new Date().toISOString().split("T")[0];

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [panelMode, setPanelMode] = useState("create");

  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [type, setType] = useState("outcome");
  const [amount, setAmount] = useState("");
  const [transactionDate, setTransactionDate] = useState(today);

  const [editingExpenseId, setEditingExpenseId] = useState(null);
  const [editDescription, setEditDescription] = useState("");
  const [editCategoryId, setEditCategoryId] = useState("");
  const [editType, setEditType] = useState("outcome");
  const [editAmount, setEditAmount] = useState("");
  const [editTransactionDate, setEditTransactionDate] = useState(today);

  const [newCategory, setNewCategory] = useState("");
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [editingCategoryName, setEditingCategoryName] = useState("");

  const loadExpenses = async () => {
    const data = await expenseApi.getAll();
    setExpenses(Array.isArray(data) ? data : []);
  };

  const loadCategories = async () => {
    const data = await categoryApi.getAll();
    const list = Array.isArray(data) ? data : [];
    setCategories(list);

    if (list.length > 0 && !categoryId) setCategoryId(String(list[0].id));
    if (list.length > 0 && !editCategoryId) setEditCategoryId(String(list[0].id));
  };

  const loadPageData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadExpenses(), loadCategories()]);
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to load expenses page");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPageData();
  }, []);

  const resetCreateForm = () => {
    setDescription("");
    setType("outcome");
    setAmount("");
    setTransactionDate(today);
    if (categories.length > 0) setCategoryId(String(categories[0].id));
  };

  const handleCreateExpense = async () => {
    if (!description || !categoryId || !type || !amount || !transactionDate) {
      alert("Please fill all required fields");
      return;
    }

    try {
      await expenseApi.create({
        description,
        category_id: Number(categoryId),
        type,
        amount: Number(amount),
        transaction_date: transactionDate,
      });

      resetCreateForm();
      await loadExpenses();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to create expense");
    }
  };

  const startEditExpense = (expense) => {
    setPanelMode("edit");
    setEditingExpenseId(expense.id);
    setEditDescription(expense.description || "");
    setEditCategoryId(String(expense.category_id));
    setEditType(expense.type || "outcome");
    setEditAmount(expense.amount ?? "");
    setEditTransactionDate(expense.transaction_date || today);
  };

  const cancelEditExpense = () => {
    setPanelMode("create");
    setEditingExpenseId(null);
    setEditDescription("");
    setEditType("outcome");
    setEditAmount("");
    setEditTransactionDate(today);
    if (categories.length > 0) setEditCategoryId(String(categories[0].id));
  };

  const handleUpdateExpense = async () => {
    if (!editingExpenseId) return;

    if (!editDescription || !editCategoryId || !editType || !editAmount || !editTransactionDate) {
      alert("Please fill all required fields");
      return;
    }

    try {
      await expenseApi.update(editingExpenseId, {
        description: editDescription,
        category_id: Number(editCategoryId),
        type: editType,
        amount: Number(editAmount),
        transaction_date: editTransactionDate,
      });

      cancelEditExpense();
      await loadExpenses();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to update expense");
    }
  };

  const handleDeleteExpense = async (id) => {
    if (!window.confirm("Are you sure you want to delete this expense?")) return;

    try {
      await expenseApi.remove(id);
      await loadExpenses();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to delete expense");
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.trim()) return;

    try {
      await categoryApi.create({ name: newCategory.trim() });
      setNewCategory("");
      await loadCategories();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to create category");
    }
  };

  const startEditCategory = (category) => {
    setEditingCategoryId(category.id);
    setEditingCategoryName(category.name);
  };

  const handleSaveCategory = async () => {
    if (!editingCategoryName.trim() || !editingCategoryId) return;

    try {
      await categoryApi.update(editingCategoryId, {
        name: editingCategoryName.trim(),
      });

      setEditingCategoryId(null);
      setEditingCategoryName("");
      await loadCategories();
      await loadExpenses();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to update category");
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm("Are you sure you want to delete this category?")) return;

    try {
      await categoryApi.remove(id);
      await loadCategories();
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to delete category");
    }
  };

  return (
    <div className="expenses-page">
      <PageHeader title="Expenses" />

      <div className="expenses-layout">
        <div className="expense-side-panel">
          {panelMode === "create" && (
            <div className="expense-form form-panel">
              <div className="expense-panel-header">
                <h3 className="section-title">Add Expense</h3>

                <button
                  className="btn btn-edit btn-action small-btn"
                  onClick={() => setPanelMode("categories")}
                >
                  <span className="btn-icon">⚙️</span>
                  <span className="btn-label">Edit Category</span>
                </button>
              </div>

              <label>Description</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} />

              <label>Category</label>
              <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>

              <label>Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                <option value="outcome">Outcome</option>
                <option value="income">Income</option>
              </select>

              <label>Amount</label>
              <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />

              <label>Date</label>
              <input
                type="date"
                value={transactionDate}
                onChange={(e) => setTransactionDate(e.target.value)}
              />

              <button className="btn btn-primary btn-full" onClick={handleCreateExpense}>
                Add Expense
              </button>
            </div>
          )}

          {panelMode === "edit" && (
            <div className="expense-form form-panel">
              <h3 className="section-title">Edit Expense</h3>

              <label>Description</label>
              <input value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />

              <label>Category</label>
              <select value={editCategoryId} onChange={(e) => setEditCategoryId(e.target.value)}>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>

              <label>Type</label>
              <select value={editType} onChange={(e) => setEditType(e.target.value)}>
                <option value="outcome">Outcome</option>
                <option value="income">Income</option>
              </select>

              <label>Amount</label>
              <input type="number" value={editAmount} onChange={(e) => setEditAmount(e.target.value)} />

              <label>Date</label>
              <input
                type="date"
                value={editTransactionDate}
                onChange={(e) => setEditTransactionDate(e.target.value)}
              />

              <div className="edit-actions">
                <button className="btn btn-primary btn-half" onClick={handleUpdateExpense}>
                  Save Changes
                </button>

                <button className="btn btn-edit btn-half" onClick={cancelEditExpense}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {panelMode === "categories" && (
            <div className="expense-form form-panel">
              <h3 className="section-title">Edit Categories</h3>

              <label>New Category</label>
              <div className="category-add-row">
                <input value={newCategory} onChange={(e) => setNewCategory(e.target.value)} />

                <button className="btn btn-primary" onClick={handleCreateCategory}>
                  Add
                </button>
              </div>

              <div className="categories-list">
                {categories.map((cat) => (
                  <div key={cat.id} className="category-row">
                    {editingCategoryId === cat.id ? (
                      <>
                        <input
                          value={editingCategoryName}
                          onChange={(e) => setEditingCategoryName(e.target.value)}
                        />

                        <button className="btn btn-primary" onClick={handleSaveCategory}>
                          Save
                        </button>
                      </>
                    ) : (
                      <>
                        <span>{cat.name}</span>

                        <div className="action-buttons">
                          <button
                            className="btn btn-edit btn-action"
                            onClick={() => startEditCategory(cat)}
                          >
                            <span className="btn-icon">✏️</span>
                            <span className="btn-label">Edit</span>
                          </button>

                          <button
                            className="btn btn-delete btn-action"
                            onClick={() => handleDeleteCategory(cat.id)}
                          >
                            <span className="btn-icon">🗑️</span>
                            <span className="btn-label">Delete</span>
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>

              <button className="btn btn-edit btn-full" onClick={() => setPanelMode("create")}>
                Back
              </button>
            </div>
          )}
        </div>

        <div className="expense-list-panel list-panel">
          <h3 className="section-title">Expense List</h3>

          {loading ? (
            <p>Loading...</p>
          ) : expenses.length === 0 ? (
            <p>No expenses found.</p>
          ) : (
            <div className="expense-table-wrapper table-scroll">
              <table className="expense-table sticky-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {expenses.map((expense) => (
                    <tr key={expense.id}>
                      <td>{expense.description}</td>
                      <td>{expense.category_name}</td>
                      <td>{expense.type}</td>
                      <td>{expense.amount}</td>
                      <td>{expense.transaction_date}</td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn btn-edit btn-action"
                            onClick={() => startEditExpense(expense)}
                          >
                            <span className="btn-icon">✏️</span>
                            <span className="btn-label">Edit</span>
                          </button>

                          <button
                            className="btn btn-delete btn-action"
                            onClick={() => handleDeleteExpense(expense.id)}
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