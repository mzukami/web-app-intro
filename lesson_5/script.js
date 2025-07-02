// HTML要素を取得して、変数に保存しておく
// constは再代入できない変数を宣言するキーワード
const numberInput = document.getElementById('numberInput'); // id="numberInput" の要素を取得
const addButton = document.getElementById('addButton');       // id="addButton" の要素を取得
const subtractButton = document.getElementById('subtractButton'); // id="subtractButton" の要素を取得
const resultDisplay = document.getElementById('result');     // id="result" の要素を取得

// --- 関数定義 ---
// 入力値を取得し、数値に変換する関数
function getInputNumber() {
    // numberInputの値（文字列）を取得
    const inputValue = numberInput.value;

    // 入力が空文字の場合は、エラーメッセージを表示して null を返す
    if (inputValue === '') {
        resultDisplay.textContent = '結果: 数値を入力してください';
        // スタイルを変更してエラーを目立たせる (任意)
        resultDisplay.style.color = 'red';
        return null; // null は「値がない」ことを示す特別な値
    }

    // 文字列を整数に変換する
    // parseInt(文字列, 10) は文字列を10進数の整数に変換する関数
    const inputNumber = parseInt(inputValue, 10);

    // 変換結果が数値でない場合 (例: "abc"などを入力した場合) はエラー
    // isNaN(値) は値が数値でない(Not a Number)場合に true を返す関数
    if (isNaN(inputNumber)) {
        resultDisplay.textContent = '結果: 有効な整数を入力してください';
        resultDisplay.style.color = 'red'; // エラーメッセージを赤色に
        return null;
    }

    // エラーがなければ、変換した数値を返す
    // 正常な場合は文字色を元に戻す
    resultDisplay.style.color = '#333'; // CSSで指定した元の色に戻す
    return inputNumber;
}

// 100を足す関数
function add100() {
    // 入力値を取得（エラーチェックも含む）
    const currentNumber = getInputNumber();

    // currentNumberが null でない場合（有効な数値が入力された場合）のみ計算
    if (currentNumber !== null) {
        const result = currentNumber + 100;
        // 結果を表示エリアに表示
        resultDisplay.textContent = '結果: ' + result;
    }
}

// 100を引く関数
function subtract100() {
    // 入力値を取得（エラーチェックも含む）
    const currentNumber = getInputNumber();

    // currentNumberが null でない場合（有効な数値が入力された場合）のみ計算
    if (currentNumber !== null) {
        const result = currentNumber - 100;
        // 結果を表示エリアに表示
        resultDisplay.textContent = '結果: ' + result;
    }
}

// --- イベントリスナーの設定 ---
// 「+100」ボタンがクリックされたら、add100関数を実行するように設定
addButton.addEventListener('click', add100);

subtractButton.addEventListener('click', subtract100); // 「-100」ボタンがクリックされたら、subtract100関数を実行するように設定