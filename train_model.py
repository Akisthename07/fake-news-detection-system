"""
train_model.py

Trains TF-IDF + Logistic Regression model and saves artifacts.
"""

import json
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from utils.text import preprocess_text


def main() -> None:
    print("Loading datasets...")
    fake_df = pd.read_csv("Fake.csv")
    true_df = pd.read_csv("True.csv")

    print(f"Fake news: {len(fake_df)}")
    print(f"Real news: {len(true_df)}")

    fake_df["label"] = 0
    true_df["label"] = 1

    print("Preprocessing text...")
    fake_df["content"] = (
        fake_df["title"].fillna("") + " " + fake_df["text"].fillna("")
    ).apply(preprocess_text)

    true_df["content"] = (
        true_df["title"].fillna("") + " " + true_df["text"].fillna("")
    ).apply(preprocess_text)

    fake_df = fake_df[fake_df["content"].str.len() > 10][["content", "label"]]
    true_df = true_df[true_df["content"].str.len() > 10][["content", "label"]]

    data = pd.concat([fake_df, true_df], ignore_index=True)
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"Total: {len(data)}")

    X = data["content"]
    y = data["label"]

    print("Splitting data (80-20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Vectorizing...")
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_df=0.80,
        min_df=2,
        ngram_range=(1, 2),
        max_features=5000,
        lowercase=True,
        strip_accents="unicode",
        sublinear_tf=True,
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print(f"Features: {X_train_vec.shape[1]}")

    print("\nTraining Naive Bayes...")
    nb_model = MultinomialNB(alpha=0.1)
    nb_model.fit(X_train_vec, y_train)
    nb_acc = accuracy_score(y_test, nb_model.predict(X_test_vec))
    print(f"Naive Bayes Accuracy: {nb_acc:.4f} ({nb_acc * 100:.2f}%)")

    print("Training Logistic Regression...")
    lr_model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        C=1.0,
        solver="lbfgs",
        class_weight="balanced",
    )
    lr_model.fit(X_train_vec, y_train)
    lr_acc = accuracy_score(y_test, lr_model.predict(X_test_vec))
    print(f"Logistic Regression Accuracy: {lr_acc:.4f} ({lr_acc * 100:.2f}%)")

    print("\nFinding optimal threshold...")
    probabilities = lr_model.predict_proba(X_test_vec)
    real_probs = probabilities[:, 1]

    best_threshold = 0.5
    best_accuracy = 0.0
    threshold_results = []

    for threshold in np.arange(0.35, 0.66, 0.02):
        preds = (real_probs >= threshold).astype(int)
        acc = accuracy_score(y_test, preds)
        threshold_results.append((threshold, acc))
        if acc > best_accuracy:
            best_accuracy = acc
            best_threshold = threshold

    print(f"Best Threshold: {best_threshold:.2f}")
    print(f"Best Accuracy: {best_accuracy:.4f} ({best_accuracy * 100:.2f}%)")

    final_preds = (real_probs >= best_threshold).astype(int)
    cm = confusion_matrix(y_test, final_preds)

    print("\n" + "=" * 70)
    print("FINAL EVALUATION")
    print("=" * 70)
    print(f"\nThreshold: {best_threshold:.2f}")
    print(f"Accuracy: {best_accuracy:.4f}")
    print(f"\nConfusion Matrix:\n{cm}")
    print("\nClassification Report:")
    print(classification_report(y_test, final_preds, target_names=["Fake", "Real"]))

    _save_visualization(nb_acc, lr_acc, threshold_results, best_threshold, cm, real_probs, y_test)

    if lr_acc >= nb_acc:
        best_model = lr_model
        selected = "Logistic Regression"
    else:
        best_model = nb_model
        selected = "Naive Bayes"

    with open("model.pkl", "wb") as file:
        pickle.dump(best_model, file)

    with open("vectorizer.pkl", "wb") as file:
        pickle.dump(vectorizer, file)

    config = {
        "optimal_threshold": round(best_threshold, 2),
        "logistic_regression_accuracy": round(lr_acc * 100, 2),
        "naive_bayes_accuracy": round(nb_acc * 100, 2),
        "selected_model": selected,
        "threshold_accuracy": round(best_accuracy * 100, 2),
    }

    with open("model_config.json", "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)

    print(f"\nModel saved: {selected}")
    print(f"Configuration saved to model_config.json")
    print("=" * 70)


def _save_visualization(nb_acc, lr_acc, threshold_results, best_threshold, cm, real_probs, y_test):
    print("\nGenerating visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax1 = axes[0, 0]
    models = ["Naive Bayes", "Logistic Regression"]
    accs = [nb_acc, lr_acc]
    bars = ax1.bar(models, accs, color=["#3b82f6", "#10b981"], alpha=0.8)
    ax1.set_ylabel("Accuracy")
    ax1.set_title("Model Accuracy Comparison", fontweight="bold")
    ax1.set_ylim(0, 1)
    for bar, acc in zip(bars, accs):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            acc + 0.02,
            f"{acc:.3f}",
            ha="center",
            fontweight="bold",
        )

    ax2 = axes[0, 1]
    thresholds = [item[0] for item in threshold_results]
    accuracies = [item[1] for item in threshold_results]
    ax2.plot(thresholds, accuracies, marker="o", linewidth=2.5, markersize=7, color="#10b981")
    ax2.axvline(
        best_threshold,
        color="#dc2626",
        linestyle="--",
        linewidth=2,
        label=f"Optimal: {best_threshold:.2f}",
    )
    ax2.set_xlabel("Decision Threshold")
    ax2.set_ylabel("Accuracy")
    ax2.set_title("Threshold Optimization", fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    ax3.imshow(cm, cmap="Blues", aspect="auto")
    ax3.set_xticks([0, 1])
    ax3.set_yticks([0, 1])
    ax3.set_xticklabels(["Fake", "Real"], fontweight="bold")
    ax3.set_yticklabels(["Fake", "Real"], fontweight="bold")
    ax3.set_ylabel("True Label", fontweight="bold")
    ax3.set_xlabel("Predicted Label", fontweight="bold")
    ax3.set_title("Confusion Matrix", fontweight="bold")
    for i in range(2):
        for j in range(2):
            ax3.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center",
                color="black",
                fontweight="bold",
                fontsize=12,
            )

    ax4 = axes[1, 1]
    real_indices = np.where(y_test == 1)[0]
    fake_indices = np.where(y_test == 0)[0]
    ax4.hist(real_probs[real_indices], bins=30, alpha=0.6, label="Real News", color="#10b981")
    ax4.hist(real_probs[fake_indices], bins=30, alpha=0.6, label="Fake News", color="#ef4444")
    ax4.axvline(
        best_threshold,
        color="#2563eb",
        linestyle="--",
        linewidth=2,
        label=f"Decision Threshold: {best_threshold:.2f}",
    )
    ax4.set_xlabel("Probability of Real News")
    ax4.set_ylabel("Frequency")
    ax4.set_title("Prediction Probability Distribution", fontweight="bold")
    ax4.legend()

    plt.tight_layout()
    plt.savefig("model_analysis.png", dpi=150, bbox_inches="tight")
    print("Saved model_analysis.png")
    plt.close()


if __name__ == "__main__":
    main()
