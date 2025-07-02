let token = localStorage.getItem("access_token");

document.addEventListener("DOMContentLoaded", () => {
  // 要素取得
  const authSection = document.getElementById("auth-section");
  const userInfoDiv = document.getElementById("user-info");
  const usernameSpan = document.getElementById("username");
  const loginFormDiv = document.getElementById("login-form");
  const registerFormDiv = document.getElementById("register-form");
  const questionsList = document.getElementById("questions-list");
  const profileEditSection = document.getElementById("profile-edit-section");
  const profileText = document.getElementById("profile-text");
  const searchInput = document.getElementById("search-input");

  const showLoggedIn = () => {
    loginFormDiv.style.display = "none";
    registerFormDiv.style.display = "none";
    userInfoDiv.style.display = "block";
    usernameSpan.textContent = localStorage.getItem("username");
    profileEditSection.style.display = "none";
    loadQuestions();
  };

  const showLoggedOut = () => {
    loginFormDiv.style.display = "block";
    registerFormDiv.style.display = "none";
    userInfoDiv.style.display = "none";
    profileEditSection.style.display = "none";
    questionsList.innerHTML = "";
  };

  // 最初の画面表示切替
  if (token) {
    showLoggedIn();
  } else {
    showLoggedOut();
  }

  // --- ログイン処理 ---
  document.getElementById("login-btn").addEventListener("click", async () => {
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    if (!username || !password) {
      alert("ユーザー名とパスワードを入力してください");
      return;
    }
    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("username", username);
        token = data.access_token;
        showLoggedIn();
      } else {
        const data = await res.json();
        alert(data.detail || "ログイン失敗");
      }
    } catch (e) {
      alert("通信エラーが発生しました");
    }
  });

  // --- 新規登録画面表示切替 ---
  document.getElementById("show-register-btn").addEventListener("click", () => {
    loginFormDiv.style.display = "none";
    registerFormDiv.style.display = "block";
  });

  // --- 新規登録処理 ---
  document.getElementById("register-btn").addEventListener("click", async () => {
    const username = document.getElementById("register-username").value.trim();
    const password = document.getElementById("register-password").value;
    if (!username || !password) {
      alert("ユーザー名とパスワードを入力してください");
      return;
    }
    try {
      const res = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
      });
      if (res.ok) {
        alert("登録成功！ログインしてください");
        document.getElementById("register-username").value = "";
        document.getElementById("register-password").value = "";
        registerFormDiv.style.display = "none";
        loginFormDiv.style.display = "block";
      } else {
        const data = await res.json();
        alert(data.detail || "登録失敗");
      }
    } catch (e) {
      alert("通信エラーが発生しました");
    }
  });

  // --- 登録キャンセル ---
  document.getElementById("cancel-register-btn").addEventListener("click", () => {
    registerFormDiv.style.display = "none";
    loginFormDiv.style.display = "block";
  });

  // --- ログアウト処理 ---
  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    token = null;
    showLoggedOut();
  });

  // --- プロフィール編集表示 ---
  document.getElementById("edit-profile-btn").addEventListener("click", async () => {
    profileEditSection.style.display = "block";
    // APIでプロフィールを取得してtextareaにセット（仮想API名 /profile）
    try {
      const res = await fetch("/profile", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        profileText.value = data.profile || "";
      } else {
        profileText.value = "";
      }
    } catch {
      profileText.value = "";
    }
  });

  // --- プロフィール保存 ---
  document.getElementById("save-profile-btn").addEventListener("click", async () => {
    const newProfile = profileText.value.trim();
    try {
      const res = await fetch("/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ profile: newProfile })
      });
      if (res.ok) {
        alert("プロフィールを保存しました");
        profileEditSection.style.display = "none";
      } else {
        alert("プロフィール保存に失敗しました");
      }
    } catch {
      alert("通信エラーが発生しました");
    }
  });

  // --- プロフィール編集キャンセル ---
  document.getElementById("cancel-profile-btn").addEventListener("click", () => {
    profileEditSection.style.display = "none";
  });

  // --- 質問一覧取得と表示 ---
  async function loadQuestions() {
    try {
      const res = await fetch("/data_with_answers");
      if (!res.ok) throw new Error("質問取得失敗");
      const data = await res.json();
      questionsList.innerHTML = "";

      data.reverse().forEach(question => {
        const li = document.createElement("li");

        const questionText = document.createElement("p");
        questionText.textContent = question.value_1;
        li.appendChild(questionText);

        // 質問評価ボタン
        if (token) {
          const rateQBtn = document.createElement("button");
          rateQBtn.textContent = `質問を評価 (${question.likes || 0})`;
          rateQBtn.addEventListener("click", () => postRating("question", question.id));
          li.appendChild(rateQBtn);
        } else {
          const likesSpan = document.createElement("span");
          likesSpan.textContent = `いいね: ${question.likes || 0}`;
          li.appendChild(likesSpan);
        }

        // 回答リスト
        const answersUl = document.createElement("ul");
        question.answers.forEach(answer => {
          const answerLi = document.createElement("li");
          answerLi.textContent = answer.content;

          if (token) {
            const rateABtn = document.createElement("button");
            rateABtn.textContent = `評価 (${answer.likes || 0})`;
            rateABtn.style.marginLeft = "10px";
            rateABtn.addEventListener("click", () => postRating("answer", answer.id));
            answerLi.appendChild(rateABtn);
          } else {
            const likesSpan = document.createElement("span");
            likesSpan.textContent = ` いいね: ${answer.likes || 0}`;
            likesSpan.style.marginLeft = "10px";
            answerLi.appendChild(likesSpan);
          }

          answersUl.appendChild(answerLi);
        });
        li.appendChild(answersUl);

        // 回答投稿フォーム
        if (token) {
          const answerForm = document.createElement("form");
          answerForm.style.marginTop = "8px";

          const answerInput = document.createElement("input");
          answerInput.type = "text";
          answerInput.placeholder = "回答を入力";
          answerInput.required = true;
          answerInput.style.width = "70%";

          const answerSubmit = document.createElement("button");
          answerSubmit.type = "submit";
          answerSubmit.textContent = "回答投稿";

          answerForm.appendChild(answerInput);
          answerForm.appendChild(answerSubmit);

          answerForm.addEventListener("submit", async e => {
            e.preventDefault();
            await postAnswer(question.id, answerInput.value);
            answerInput.value = "";
          });

          li.appendChild(answerForm);
        }

        questionsList.appendChild(li);
      });
    } catch (e) {
      alert("質問の読み込みに失敗しました");
    }
  }

  // --- 回答投稿 ---
  async function postAnswer(questionId, content) {
    if (!content.trim()) {
      alert("回答を入力してください");
      return;
    }
    try {
      const res = await fetch("/answers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ question_id: questionId, content })
      });
      if (res.ok) {
        await loadQuestions();
      } else {
        const data = await res.json();
        alert(data.detail || "回答投稿失敗");
      }
    } catch {
      alert("通信エラーが発生しました");
    }
  }

  // --- 評価投稿 ---
  async function postRating(targetType, targetId) {
    try {
      const res = await fetch("/ratings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ target_type: targetType, target_id: targetId })
      });
      if (res.ok) {
        await loadQuestions();
      } else {
        const data = await res.json();
        alert(data.detail || "評価失敗");
      }
    } catch {
      alert("通信エラーが発生しました");
    }
  }

  // --- 検索処理 ---
  document.getElementById("search-btn").addEventListener("click", async () => {
    const keyword = searchInput.value.trim();
    if (!keyword) {
      alert("検索キーワードを入力してください");
      return;
    }
    try {
      const res = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
      if (!res.ok) throw new Error("検索失敗");
      const data = await res.json();

      questionsList.innerHTML = "";
      data.forEach(q => {
        const li = document.createElement("li");
        const qText = document.createElement("p");
        qText.textContent = q.value_1;
        li.appendChild(qText);

        // 省略: 質問評価・回答リストはloadQuestions同様に実装してもよい

        questionsList.appendChild(li);
      });
    } catch {
      alert("検索に失敗しました");
    }
  });

});
