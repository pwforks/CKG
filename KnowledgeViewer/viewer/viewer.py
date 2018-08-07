import itertools
from KnowledgeConnector import graph_controler
from KnowledgeViewer.queries import *
from KnowledgeViewer.plots import basicFigures as figure
from KnowledgeViewer.analyses import basicAnalysis as analyses

def getDBresults(query, driver, replace=[]):
    for r,by in replace:
        query = query.replace(r,by)
    results = graph_controler.getCursorData(driver, query)
    print(results)
    return results

def getPlot(name, data, identifier, title, args = {}):
    plot = None
    if name == "basicTable":
        colors = ('#C2D4FF','#F5F8FF')
        attr =  {'width':800, 'height':300, 'font':12}
        subset = None
        if "colors" in args:
            colors = args["colors"]
        if "attr" in args:
            attr = args["attr"]
        if "subset" in args:
            subset = args["subset"]
        plot = figure.getBasicTable(data, identifier, title, colors=colors, subset=subset, plot_attr=attr)
    elif name == "basicBarPlot":
        print(data.columns)
        if "x" in data.columns and "y" in data.columns and "name" in data.columns:
            x_title = "x"
            y_title = "y"
            if "x_title" in args:
                x_title = args["x_title"]
            if "y_title" in args:
                y_title = args["y_title"]
            plot = figure.getBarPlotFigure(data, identifier, title, x_title, y_title)
    elif name == "scatterPlot":
        if "x" in data.columns and "y" in data.columns and "name" in data.columns:
            x_title = "x"
            y_title = "y"
            if "x_title" in args:
                x_title = args["x_title"]
            if "y_title" in args:
                y_title = args["y_title"]
            plot = figure.getScatterPlotFigure(data, identifier, title, x_title, y_title)
    elif name == "volcanoPlot":
        plot = []
        alpha = 0.05
        lfc = 1.0
        if "alpha" in args:
            alpha = args["alpha"]
        if "lfc" in args:
            lfc = args["lfc"]
        for pair in data:
            signature = data[pair]
            p = figure.runVolcano(identifier+"_"+pair[0]+"_vs_"+pair[1], signature, lfc=lfc, alpha=alpha, title=title+" "+pair[0]+" vs "+pair[1])
            plot.append(p)
    return plot

def preprocessData(data, qtype, args):
    if qtype == "proteomics":
        imputation = True
        method = "distribution"
        missing_method = 'percentage'
        missing_max = 0.3
        
        if "imputation" in args:
            imputation = args["imputation"]
        if "method" in args:
            method = args["method"]
        if "missing_method" in args:
            missing_method = args["missing_method"]
        if "missing_max" in args:
            missing_max = args["missing_max"]
        data = analyses.get_measurements_ready(data, imputation = imputation, method = method, missing_method = missing_method, missing_max = missing_max)

    return data

def getAnalysisResults(data, analysis_type, args):
    result = None
    if analysis_type == "pca":
        components = 2
        if "components" in args:
            components = args["components"]
        result, args = analyses.runPCA(data, components)
    elif analysis_type == "tsne":
        components = 2
        perplexity = 40
        n_iter = 1000
        init='pca'
        if "components" in args:
            components = args["components"]
        if "perplexity" in args:
            perplexity = args["perplexity"]
        if "n_iter" in args:
            n_iter = args["n_iter"]
        if "init" in args:
            init = args["init"]
        result, args = analyses.runTSNE(data, components=components, perplexity=perplexity, n_iter=n_iter, init=init)
    elif analysis_type == "umap":
        n_neighbors=10
        min_dist=0.3
        metric='cosine'
        if "n_neighbors" in args:
            n_neighbors = args["n_neighbors"]
        if "min_dist" in args:
            min_dist = args["min_dist"]
        if "metric" in args:
            metric = args["metric"]
        result, args = analyses.runUMAP(data, n_neighbors=n_neighbors, min_dist=min_dist, metric=metric)
    elif analysis_type == 'ttest':
        result = {}
        alpha = 0.05
        if "alpha" in args:
            alpha = args["alpha"]
        for pair in itertools.combinations(data.group.unique(),2):
            ttest_result = analyses.ttest(data, pair[0], pair[1], alpha = 0.05)
            result[pair] = ttest_result
    return result, args

def view(title, section_query, analysis_types, plot_name, args):
    result = None
    plots = []
    print(analysis_types)
    driver = graph_controler.getGraphDatabaseConnectionConfiguration()
    if title in ["project","proteomics"]:
        replace = []
        queries = project_cypher.queries
        replacement = "PROJECTID"
        if "id" in args:
            replace.append((replacement, args["id"]))
            print("Here",section_query)
            query = None
            if section_query.upper() in queries:
                plot_title, query = queries[section_query.upper()]
                data = getDBresults(query, driver, replace)
                result = data
                if not data.empty:
                    if len(analysis_types) >= 1:
                        processed_data = preprocessData(data, title, args)
                        for analysis_type in analysis_types:
                            print(analysis_type)
                            result, new_args = getAnalysisResults(processed_data, analysis_type, args)
                            if result is not None:
                                print("plotting")
                                plot = getPlot(plot_name, result, "project_"+section_query+"_"+analysis_type, analysis_type.capitalize(), new_args)
                                if type(plot) == list:
                                    plots.extend(plot)
                                else:
                                    plots.append(plot)
                    else:
                        plot = getPlot(plot_name, result, "project_"+section_query, plot_title, args)
                        plots.append(plot)
    elif title == "import":
        pass
    
    return plots
    

    
