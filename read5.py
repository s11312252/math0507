@app.route("/read2", methods=["GET", "POST"])
def read2():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        
        results = []
        for doc in docs:
            teacher = doc.to_dict()
            if "name" in teacher and keyword in teacher["name"]:
                results.append(teacher)
        
        return render_template("searchteacher.html", keyword=keyword, results=results)
    
    return render_template("searchteacher.html", keyword=None, results=None)
